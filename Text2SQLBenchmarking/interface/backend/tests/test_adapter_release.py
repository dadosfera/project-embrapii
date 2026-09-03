from __future__ import annotations

from types import SimpleNamespace

import pytest

from interface.backend.adapters.factory import create_adapter
from interface.backend.adapters import release as release_module
from interface.backend.adapters.release import (
    cleanup_compute_memory,
    release_raw_model_generator,
    release_vanna_generator,
)
from interface.backend.domain.capabilities import ApplicationMode
from interface.backend.tests.adapter_support import DependencyRecorder, RecordingFactory, configuration, create_project_root


class FakeCuda:
    def __init__(self, available: bool):
        self.available = available
        self.calls: list[str] = []
    def is_available(self): return self.available
    def empty_cache(self): self.calls.append("empty_cache")
    def ipc_collect(self): self.calls.append("ipc_collect")


class FakeTorchCore:
    def __init__(self, callback=None):
        self._cuda_clearCublasWorkspaces = callback


def test_cuda_cleanup_is_defensive_for_cuda_and_cpu_only():
    collected: list[str] = []
    cuda = FakeCuda(True)
    cleanup_compute_memory(torch_module=SimpleNamespace(cuda=cuda), collector=lambda: collected.append("gc"))
    assert collected == ["gc"] and cuda.calls == ["empty_cache", "ipc_collect"]
    cpu = FakeCuda(False)
    cleanup_compute_memory(torch_module=SimpleNamespace(cuda=cpu), collector=lambda: None)
    assert cpu.calls == []


def test_cuda_cleanup_clears_cublas_workspace_when_supported():
    calls: list[str] = []
    cuda = FakeCuda(True)
    torch_module = SimpleNamespace(
        cuda=cuda,
        _C=FakeTorchCore(lambda: calls.append("cublas")),
    )

    cleanup_compute_memory(torch_module=torch_module, collector=lambda: calls.append("gc"))

    assert calls == ["gc", "cublas"]
    assert cuda.calls == ["empty_cache", "ipc_collect"]


def test_cuda_cleanup_is_resilient_to_missing_or_failing_cublas_cleanup():
    for cublas in (None, lambda: (_ for _ in ()).throw(RuntimeError("synthetic"))):
        cuda = FakeCuda(True)
        cleanup_compute_memory(
            torch_module=SimpleNamespace(cuda=cuda, _C=FakeTorchCore(cublas)),
            collector=lambda: None,
        )
        assert cuda.calls == ["empty_cache", "ipc_collect"]


def test_raw_release_uses_known_pipeline_contract_without_move_to_cpu():
    moves: list[str] = []
    model = SimpleNamespace(to=lambda device: moves.append(device))
    pipe = SimpleNamespace(model=model, tokenizer=object())
    engine = SimpleNamespace(dispose=lambda: moves.append("disposed"))
    generator = SimpleNamespace(pipe=pipe, engine=engine, _schema_cache={"x": "y"})

    release_raw_model_generator(generator)
    release_raw_model_generator(generator)

    assert moves == ["disposed"]
    assert pipe.model is None and pipe.tokenizer is None
    assert generator.pipe is None and generator.engine is None and generator._schema_cache == {}


def test_vanna_release_clears_real_chroma_contract_before_client(monkeypatch):
    events: list[tuple[str, dict[str, object]]] = []
    snapshots = iter([(1, ("first",)), (0, ())])
    monkeypatch.setattr(release_module, "shared_system_cache_snapshot", lambda: next(snapshots))
    monkeypatch.setattr(
        release_module,
        "log_runtime_event",
        lambda event, **fields: events.append((event, fields)),
    )
    clear_calls: list[str] = []
    client = SimpleNamespace(clear_system_cache=lambda: clear_calls.append("clear"))
    engine = SimpleNamespace(dispose=lambda: clear_calls.append("dispose"))
    vn = SimpleNamespace(
        documentation_collection=object(), ddl_collection=object(), sql_collection=object(),
        chroma_client=client, embedding_function=object(), model=object(), tokenizer=object(), engine=engine,
    )
    generator = SimpleNamespace(vn=vn)

    release_vanna_generator(generator)
    release_vanna_generator(generator)

    assert clear_calls == ["dispose", "clear"]
    assert generator.vn is None
    assert [event for event, _ in events] == [
        "vanna.chromadb.systems.before", "vanna.chromadb.systems.clear", "vanna.chromadb.systems.after"
    ]


def test_vanna_release_feature_detects_missing_chroma_cache_api(monkeypatch):
    monkeypatch.setattr(release_module, "shared_system_cache_snapshot", lambda: (None, ()))
    events: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(release_module, "log_runtime_event", lambda event, **fields: events.append((event, fields)))
    vn = SimpleNamespace(
        documentation_collection=object(), ddl_collection=object(), sql_collection=object(),
        chroma_client=object(), embedding_function=object(), model=object(), tokenizer=object(), engine=None,
    )

    release_vanna_generator(SimpleNamespace(vn=vn))

    assert ("vanna.chromadb.systems.clear", {"supported": False}) in events
