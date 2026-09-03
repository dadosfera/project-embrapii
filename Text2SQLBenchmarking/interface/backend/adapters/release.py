"""Liberação defensiva de referências pesadas dos geradores legados."""

from __future__ import annotations

import gc
from typing import Any, Callable

from interface.backend.diagnostics import (
    log_runtime_event,
    shared_system_cache_snapshot,
)


def release_legacy_references(root: object) -> None:
    """Compatibilidade mínima para geradores controlados pelo adapter.

    Esta função não percorre mais ``__dict__`` de bibliotecas de terceiros nem
    move pesos para CPU. Adapters com contratos conhecidos fazem seu cleanup
    específico abaixo.
    """

    for name in ("pipe", "pipeline", "agent", "generator", "client", "executor"):
        if hasattr(root, name):
            setattr(root, name, None)


def _dispose_engine(value: object) -> None:
    dispose = getattr(value, "dispose", None)
    if callable(dispose):
        dispose()


def release_raw_model_generator(generator: object) -> None:
    """Libera somente os contratos conhecidos de ``src.rawmodel.RawModel``."""

    engine = getattr(generator, "engine", None)
    if engine is not None:
        _dispose_engine(engine)
    # ``pipe`` é controlado por RawModel; os dois atributos são o contrato
    # público do pipeline Transformers e precisam ser soltos para destruir os
    # pesos, sem a cópia dispendiosa para CPU.
    pipe = getattr(generator, "pipe", None)
    if pipe is not None:
        for name in ("model", "tokenizer"):
            if hasattr(pipe, name):
                setattr(pipe, name, None)
    for name in ("pipe", "engine", "client", "_schema_cache"):
        if hasattr(generator, name):
            setattr(generator, name, None if name != "_schema_cache" else {})


def release_vanna_generator(generator: object) -> None:
    """Libera o contrato real de Vanna 0.5/Chroma 0.5 antes do workspace."""

    vn = getattr(generator, "vn", None)
    if vn is None:
        return
    engine = getattr(vn, "engine", None)
    if engine is not None:
        _dispose_engine(engine)

    # ChromaDB_VectorStore realmente expõe estes três collections e o client.
    # Soltar collections antes do client evita que seus handles retenham o
    # System persistente durante a limpeza do diretório do workspace.
    for name in ("documentation_collection", "ddl_collection", "sql_collection"):
        if hasattr(vn, name):
            setattr(vn, name, None)
    client = getattr(vn, "chroma_client", None)
    before, identifiers = shared_system_cache_snapshot()
    log_runtime_event(
        "vanna.chromadb.systems.before",
        systems=before,
        identifiers=list(identifiers),
    )
    clear_cache = getattr(client, "clear_system_cache", None)
    if callable(clear_cache):
        clear_cache()
        log_runtime_event("vanna.chromadb.systems.clear", supported=True)
    else:
        log_runtime_event("vanna.chromadb.systems.clear", supported=False)
    after, after_identifiers = shared_system_cache_snapshot()
    log_runtime_event(
        "vanna.chromadb.systems.after",
        systems=after,
        identifiers=list(after_identifiers),
    )

    for name in ("chroma_client", "embedding_function", "model", "tokenizer", "engine"):
        if hasattr(vn, name):
            setattr(vn, name, None)
    if hasattr(generator, "vn"):
        setattr(generator, "vn", None)


def cleanup_compute_memory(*, torch_module: Any | None = None, collector: Callable[[], object] = gc.collect) -> None:
    """Coleta RAM e libera caches CUDA quando disponíveis, sem exigir torch."""

    collector()
    if torch_module is None:
        try:
            import torch as torch_module  # type: ignore[no-redef]
        except Exception:
            return
    cuda = getattr(torch_module, "cuda", None)
    available = getattr(cuda, "is_available", None)
    if cuda is None or not callable(available):
        return
    try:
        if not available():
            return
    except Exception:
        return

    # Workspaces cuBLAS podem manter segmentos inactive_split no caching
    # allocator mesmo depois de modelo/pipeline terem sido desacoplados.
    # Trata-se de API interna: só a usamos por feature detection e nunca como
    # requisito para que a liberação principal seja bem-sucedida.
    clear_cublas = getattr(getattr(torch_module, "_C", None), "_cuda_clearCublasWorkspaces", None)
    if callable(clear_cublas):
        try:
            clear_cublas()
        except Exception:
            pass

    empty_cache = getattr(cuda, "empty_cache", None)
    if callable(empty_cache):
        try:
            empty_cache()
        except Exception:
            pass
    ipc_collect = getattr(cuda, "ipc_collect", None)
    if callable(ipc_collect):
        try:
            ipc_collect()
        except Exception:
            pass
