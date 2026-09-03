#!/usr/bin/env python3
"""Smoke real e controlado do lifecycle de adapters da interface.

Não chama os scripts de benchmark, não grava ``resources/out`` e nunca executa
a SQL gerada. O Vanna ainda lê o schema durante sua construção normal, como o
adapter de produção, para que o teste cubra o lifecycle real.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
from time import time
from types import SimpleNamespace

# O comando documentado executa este arquivo por caminho; nesse caso Python
# adiciona ``interface/tools`` ao sys.path, não a raiz do projeto.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from interface.backend.adapters.release import release_vanna_generator
from interface.backend.adapters.workspace import RuntimeWorkspace
from interface.backend.diagnostics import sanitize_message
from interface.backend.domain.capabilities import (
    ApplicationMode,
    ConfigurationSelection,
    LibraryId,
    ModelFamily,
    list_models,
)
from interface.backend.runtime.key import RuntimeKey
from interface.backend.runtime.manager import ModelManager
from interface.backend.runtime.workspace_cleanup import cleanup_backend_workspace


QUESTION = "Quantas internações foram registradas no total?"
ROOT = PROJECT_ROOT


class _NoopEmbedding:
    """Evita download de embedding no diagnóstico Chroma sem fazer inserts."""

    def __call__(self, input):
        return [[0.0] for _ in input]


def _emit(event: str, **fields: object) -> None:
    record = {"timestamp": time(), "event": event, **fields}
    print(json.dumps(record, ensure_ascii=False, sort_keys=True), flush=True)


def _safe(value: object) -> str:
    return hashlib.sha256(str(value).encode()).hexdigest()[:12]


def _memory() -> dict[str, object]:
    result: dict[str, object] = {}
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip().splitlines()
        result["vram_mib"] = [line.strip() for line in output]
    except (OSError, subprocess.CalledProcessError):
        result["vram_mib"] = "unavailable"
    try:
        pages = os.sysconf("SC_PAGE_SIZE")
        resident = int(Path("/proc/self/statm").read_text().split()[1]) * pages
        result["process_rss_mib"] = round(resident / 1024 / 1024, 1)
        meminfo = dict(
            line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines() if ":" in line
        )
        result["system_available_mib"] = round(int(meminfo["MemAvailable"].split()[0]) / 1024, 1)
    except (OSError, KeyError, ValueError, IndexError):
        result["process_rss_mib"] = "unavailable"
    return result


def _cuda_allocator_memory() -> dict[str, object]:
    """Métricas do allocator no mesmo processo, após liberar o runtime."""

    try:
        import torch

        if not torch.cuda.is_available():
            return {"cuda_allocator": "unavailable"}
        stats = torch.cuda.memory_stats()
        return {
            "allocated_mib": round(torch.cuda.memory_allocated() / 1024 / 1024, 3),
            "reserved_mib": round(torch.cuda.memory_reserved() / 1024 / 1024, 3),
            "inactive_split_mib": round(
                stats.get("inactive_split_bytes.all.current", 0) / 1024 / 1024,
                3,
            ),
        }
    except Exception:
        return {"cuda_allocator": "unavailable"}


def _available_models() -> tuple[str, str]:
    candidates: list[tuple[int, str]] = []
    for model in list_models():
        if model.family is not ModelFamily.GENERAL:
            continue
        directory = ROOT / "local_models" / model.id.replace("/", "-")
        if directory.is_dir() and any(directory.iterdir()):
            size = sum(path.stat().st_size for path in directory.rglob("*") if path.is_file())
            candidates.append((size, model.id))
    candidates.sort()
    _emit("models.available", models=[model for _, model in candidates])
    if len(candidates) < 2:
        raise RuntimeError("menos de dois modelos VannaAI compatíveis estão disponíveis localmente")
    return candidates[0][1], candidates[1][1]


def _key(library: LibraryId, model_id: str, hf_token: str | None) -> RuntimeKey:
    context = "none" if library is LibraryId.VANNA_AI else "default"
    return RuntimeKey.from_configuration(
        ConfigurationSelection(database="sih_database", library=library.value, model_id=model_id, context=context),
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token=hf_token,
        project_root=ROOT,
    )


def _switch(library: LibraryId, models: tuple[str, str], hf_token: str | None) -> bool:
    manager = ModelManager()
    label = library.value
    successful = True
    try:
        for name, model in (("A", models[0]), ("B", models[1]), ("A-reload", models[0])):
            key = _key(library, model, hf_token)
            _emit(f"{label}.{name}.load.begin", runtime_key=_safe(key), **_memory())
            try:
                adapter = manager.get_or_load(key, hf_token=hf_token)
                _emit(f"{label}.{name}.load.success", state=manager.state.value, **_memory())
                generated = adapter.generate(QUESTION)
                manager.mark_used()
                _emit(f"{label}.{name}.generate.success", sql_length=len(generated.sql), **_memory())
            except Exception as exc:
                successful = False
                _emit(
                    f"{label}.{name}.FAILED",
                    exception=type(exc).__name__,
                    detail=getattr(exc, "internal_detail", "sanitized"),
                    state=manager.state.value,
                    runtime_loaded=manager.adapter is not None,
                    **_memory(),
                )
                break
    finally:
        _emit(f"{label}.unload.begin", state=manager.state.value, **_memory())
        try:
            manager.shutdown()
            _emit(
                f"{label}.unload.success",
                state=manager.state.value,
                **_cuda_allocator_memory(),
                **_memory(),
            )
        except Exception as exc:
            successful = False
            _emit(f"{label}.unload.FAILED", exception=type(exc).__name__, **_memory())
    return successful


def _chroma_only() -> bool:
    try:
        from vanna.chromadb import ChromaDB_VectorStore
    except Exception as exc:
        _emit("chroma.import.FAILED", exception=type(exc).__name__)
        return False

    class ChromaOnlyStore(ChromaDB_VectorStore):
        """Implementa só os abstratos de VannaBase; não cria nem usa LLM."""

        def system_message(self, message):
            return {"role": "system", "content": message}

        def user_message(self, message):
            return {"role": "user", "content": message}

        def assistant_message(self, message):
            return {"role": "assistant", "content": message}

        def submit_prompt(self, prompt, **kwargs):
            raise RuntimeError("ChromaOnlyStore não executa prompts")

    success = True
    for name in ("A", "B", "C"):
        workspace: RuntimeWorkspace | None = None
        try:
            workspace = RuntimeWorkspace.create(project_root=ROOT)
            _emit("chroma.workspace.begin", label=name, workspace=_safe(workspace.working_directory), **_memory())
            with workspace.activate():
                store = ChromaOnlyStore(
                    config={"path": "./vanna_storage", "embedding_function": _NoopEmbedding()}
                )
            _emit("chroma.init.success", label=name)
            release_vanna_generator(SimpleNamespace(vn=store))
            _emit("chroma.release.success", label=name)
        except Exception as exc:
            success = False
            _emit("chroma.FAILED", label=name, exception=type(exc).__name__, detail=sanitize_message(exc))
            break
        finally:
            if workspace is not None:
                try:
                    cleanup_backend_workspace(workspace)
                    _emit("chroma.cleanup.success", label=name)
                except Exception as exc:
                    success = False
                    _emit("chroma.cleanup.FAILED", label=name, exception=type(exc).__name__)
    return success


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    token = os.getenv("HF_TOKEN")
    _emit("smoke.begin", **_memory())
    models = _available_models()
    chroma_ok = _chroma_only()
    raw_ok = _switch(LibraryId.RAW_MODEL, models, token)
    vanna_ok = _switch(LibraryId.VANNA_AI, models, token)
    _emit("smoke.end", chroma_ok=chroma_ok, raw_ok=raw_ok, vanna_ok=vanna_ok, **_memory())
    return 0 if chroma_ok and raw_ok and vanna_ok else 1


if __name__ == "__main__":
    sys.exit(main())
