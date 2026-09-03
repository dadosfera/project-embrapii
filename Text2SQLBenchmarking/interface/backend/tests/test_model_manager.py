from __future__ import annotations

import math
from pathlib import Path
import sys
import weakref

import pytest

from interface.backend.adapters.workspace import RuntimeWorkspace
from interface.backend.domain.capabilities import ApplicationMode
from interface.backend.runtime.key import RuntimeKey
from interface.backend.runtime.manager import (
    ModelManager,
    RuntimeManagerError,
    RuntimeManagerErrorCode,
    RuntimeState,
)
from interface.backend.runtime.workspace_cleanup import cleanup_backend_workspace
from interface.backend.tests.adapter_support import configuration, create_project_root


REAL_GENERATOR_MODULES = {
    "src.rawmodel",
    "src.vannaai",
    "src.premsqlAgente",
    "src.xiyansql",
}


class FakeClock:
    def __init__(self, value: float = 0.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


class FakeAdapter:
    def __init__(
        self,
        workspace: RuntimeWorkspace,
        events: list[str],
        *,
        load_error: Exception | None = None,
        release_error: Exception | None = None,
    ) -> None:
        self.workspace = workspace
        self.events = events
        self.load_error = load_error
        self.release_error = release_error
        self.load_calls = 0
        self.release_calls = 0

    def load(self) -> None:
        self.load_calls += 1
        self.events.append("load")
        if self.load_error is not None:
            raise self.load_error

    def release(self) -> None:
        self.release_calls += 1
        self.events.append("release")
        if self.release_error is not None:
            raise self.release_error


class FakeAdapterFactory:
    def __init__(self, events: list[str], outcomes: list[dict[str, object]] | None = None):
        self.events = events
        self.outcomes = outcomes or []
        self.adapters: list[FakeAdapter] = []

    def __call__(
        self,
        key: RuntimeKey,
        workspace: RuntimeWorkspace,
        hf_token: str | None,
    ) -> FakeAdapter:
        self.events.append("factory")
        options = self.outcomes.pop(0) if self.outcomes else {}
        adapter = FakeAdapter(workspace, self.events, **options)
        self.adapters.append(adapter)
        return adapter


def _key(root: Path, *, seed: int = 42) -> RuntimeKey:
    return RuntimeKey.from_configuration(
        configuration(),
        ApplicationMode.CHAT,
        random_seed=seed,
        hf_token="synthetic-token",
        project_root=root,
    )


def _workspace_factory(root: Path, captured: list[RuntimeWorkspace]):
    def create() -> RuntimeWorkspace:
        workspace = RuntimeWorkspace.create(project_root=root)
        captured.append(workspace)
        return workspace

    return create


def _manager(root: Path, *, clock=None, factory=None, cleanup=None, ttl=600.0):
    events: list[str] = []
    workspaces: list[RuntimeWorkspace] = []
    selected_factory = factory or FakeAdapterFactory(events)
    selected_cleanup = cleanup or cleanup_backend_workspace
    manager = ModelManager(
        adapter_factory=selected_factory,
        workspace_factory=_workspace_factory(root, workspaces),
        clock=clock or FakeClock(),
        workspace_cleanup=selected_cleanup,
        ttl_seconds=ttl,
    )
    return manager, selected_factory, events, workspaces


def test_first_request_loads_adapter_and_same_key_reuses_it(tmp_path):
    root = create_project_root(tmp_path / "project")
    clock = FakeClock()
    manager, factory, _, _ = _manager(root, clock=clock)
    key = _key(root)

    assert manager.state is RuntimeState.EMPTY
    assert manager.current_key is None
    assert manager.adapter is None
    assert manager.last_used is None

    first = manager.get_or_load(key, hf_token="synthetic-token")
    clock.value = 12.0
    second = manager.get_or_load(key, hf_token="synthetic-token")

    assert first is second
    assert len(factory.adapters) == 1
    assert factory.adapters[0].load_calls == 1
    assert manager.last_used == 12.0
    assert manager.state is RuntimeState.READY


def test_mark_used_updates_the_idle_reference_after_an_operation(tmp_path):
    root = create_project_root(tmp_path / "project")
    clock = FakeClock()
    manager, _, _, _ = _manager(root, clock=clock)
    manager.get_or_load(_key(root), hf_token="synthetic-token")

    clock.value = 21.0
    manager.mark_used()

    assert manager.last_used == 21.0


def test_different_key_releases_before_loading_new_runtime(tmp_path):
    root = create_project_root(tmp_path / "project")
    events: list[str] = []
    factory = FakeAdapterFactory(events)
    workspaces: list[RuntimeWorkspace] = []

    def cleanup(workspace: RuntimeWorkspace) -> None:
        events.append("cleanup")
        cleanup_backend_workspace(workspace)

    manager = ModelManager(
        adapter_factory=factory,
        workspace_factory=_workspace_factory(root, workspaces),
        workspace_cleanup=cleanup,
    )
    first_key = _key(root, seed=42)
    second_key = _key(root, seed=43)
    first = manager.get_or_load(first_key, hf_token="synthetic-token")
    second = manager.get_or_load(second_key, hf_token="synthetic-token")

    assert first is not second
    assert events == ["factory", "load", "release", "cleanup", "factory", "load"]
    assert manager.current_key == second_key
    assert not workspaces[0].working_directory.exists()


def test_release_failure_prevents_safe_runtime_swap(tmp_path):
    root = create_project_root(tmp_path / "project")
    events: list[str] = []
    factory = FakeAdapterFactory(events, [{"release_error": RuntimeError("synthetic")}])
    manager = ModelManager(
        adapter_factory=factory,
        workspace_factory=_workspace_factory(root, []),
    )
    first_key = _key(root, seed=42)
    manager.get_or_load(first_key, hf_token="synthetic-token")

    with pytest.raises(RuntimeManagerError) as raised:
        manager.get_or_load(_key(root, seed=43), hf_token="synthetic-token")

    assert raised.value.code is RuntimeManagerErrorCode.RUNTIME_RELEASE_ERROR
    assert len(factory.adapters) == 1
    assert manager.current_key == first_key
    assert manager.adapter is factory.adapters[0]
    assert manager.state is RuntimeState.FAILED


def test_new_load_failure_does_not_leave_ready_runtime_or_restore_old(tmp_path):
    root = create_project_root(tmp_path / "project")
    events: list[str] = []
    factory = FakeAdapterFactory(
        events,
        [{}, {"load_error": RuntimeError("synthetic load failure")}],
    )
    workspaces: list[RuntimeWorkspace] = []
    manager = ModelManager(
        adapter_factory=factory,
        workspace_factory=_workspace_factory(root, workspaces),
    )
    first_key = _key(root, seed=42)
    manager.get_or_load(first_key, hf_token="synthetic-token")

    with pytest.raises(RuntimeManagerError) as raised:
        manager.get_or_load(_key(root, seed=43), hf_token="synthetic-token")

    assert raised.value.code is RuntimeManagerErrorCode.RUNTIME_LOAD_ERROR
    assert manager.state is RuntimeState.EMPTY
    assert manager.adapter is None
    assert manager.current_key is None
    assert factory.adapters[0].release_calls == 1
    assert factory.adapters[1].release_calls == 1
    assert not workspaces[0].working_directory.exists()
    assert not workspaces[1].working_directory.exists()

    recovered = manager.get_or_load(_key(root, seed=44), hf_token="synthetic-token")
    assert recovered is factory.adapters[2]
    assert manager.state is RuntimeState.READY


def test_chat_qwen3_to_qwen25_swap_does_not_retain_both_adapters(tmp_path):
    root = create_project_root(tmp_path / "project")
    manager, factory, events, _ = _manager(root)
    qwen3 = RuntimeKey.from_configuration(
        configuration(model_id="Qwen/Qwen3-32B"), ApplicationMode.CHAT, random_seed=42,
        hf_token="synthetic-token", project_root=root,
    )
    qwen25 = _key(root)
    manager.get_or_load(qwen3, hf_token="synthetic-token")
    manager.get_or_load(qwen25, hf_token="synthetic-token")
    assert events == ["factory", "load", "release", "factory", "load"]
    assert manager.adapter is factory.adapters[1] and factory.adapters[0].release_calls == 1


def test_expiration_uses_injected_monotonic_clock(tmp_path):
    root = create_project_root(tmp_path / "project")
    clock = FakeClock()
    manager, factory, _, _ = _manager(root, clock=clock, ttl=600.0)
    key = _key(root)
    manager.get_or_load(key, hf_token="synthetic-token")

    clock.value = 599.9
    assert not manager.expire_if_idle()
    assert manager.state is RuntimeState.READY
    clock.value = 600.0
    assert manager.expire_if_idle()
    assert factory.adapters[0].release_calls == 1
    assert manager.state is RuntimeState.EMPTY


def test_shutdown_releases_once_and_is_idempotent(tmp_path):
    root = create_project_root(tmp_path / "project")
    manager, factory, _, _ = _manager(root)
    manager.get_or_load(_key(root), hf_token="synthetic-token")

    manager.shutdown()
    manager.shutdown()

    assert factory.adapters[0].release_calls == 1
    assert manager.state is RuntimeState.EMPTY


def test_backend_workspace_is_removed_but_caller_workspace_is_preserved(tmp_path):
    root = create_project_root(tmp_path / "project")
    manager, _, _, backend_workspaces = _manager(root)
    manager.get_or_load(_key(root), hf_token="synthetic-token")
    backend_workspace = backend_workspaces[0]
    manager.shutdown()
    assert not backend_workspace.working_directory.exists()

    caller_directory = root / "interface" / ".runtime" / "adapters" / "caller"
    caller_workspace = RuntimeWorkspace.create(
        project_root=root,
        runtime_directory=caller_directory,
    )
    events: list[str] = []
    factory = FakeAdapterFactory(events)
    manager = ModelManager(
        adapter_factory=factory,
        workspace_factory=lambda: caller_workspace,
        workspace_cleanup=lambda workspace: (_ for _ in ()).throw(
            AssertionError("workspace do caller não deve ser limpo")
        ),
    )
    manager.get_or_load(_key(root), hf_token="synthetic-token")
    manager.shutdown()

    assert caller_workspace.working_directory.exists()
    assert (caller_workspace.working_directory / "local_models").is_symlink()


def test_cleanup_never_follows_local_models_or_external_links(tmp_path):
    root = create_project_root(tmp_path / "project")
    models_marker = root / "local_models" / "model.marker"
    models_marker.write_text("model synthetic", encoding="utf-8")
    workspace = RuntimeWorkspace.create(project_root=root)
    external = tmp_path / "external"
    external.mkdir()
    external_marker = external / "marker"
    external_marker.write_text("outside", encoding="utf-8")
    (workspace.working_directory / "outside-link").symlink_to(
        external,
        target_is_directory=True,
    )

    cleanup_backend_workspace(workspace)

    assert not workspace.working_directory.exists()
    assert models_marker.read_text(encoding="utf-8") == "model synthetic"
    assert external_marker.read_text(encoding="utf-8") == "outside"


def test_manager_errors_are_safe_when_load_or_cleanup_fail(tmp_path):
    root = create_project_root(tmp_path / "project")
    secret = "synthetic-secret"
    path = tmp_path / "private-path"
    events: list[str] = []
    factory = FakeAdapterFactory(events, [{"load_error": RuntimeError(f"{secret} {path}")}])
    manager = ModelManager(
        adapter_factory=factory,
        workspace_factory=_workspace_factory(root, []),
    )

    with pytest.raises(RuntimeManagerError) as raised:
        manager.get_or_load(_key(root), hf_token="synthetic-token")

    assert raised.value.code is RuntimeManagerErrorCode.RUNTIME_LOAD_ERROR
    assert secret not in str(raised.value)
    assert str(path) not in str(raised.value)


def test_cleanup_failure_is_structured_and_keeps_runtime_for_diagnosis(tmp_path):
    root = create_project_root(tmp_path / "project")
    secret = "synthetic-cleanup-secret"
    private_path = tmp_path / "private-cleanup-path"
    manager, factory, _, _ = _manager(
        root,
        cleanup=lambda workspace: (_ for _ in ()).throw(
            RuntimeError(f"{secret} {private_path}")
        ),
    )
    key = _key(root)
    manager.get_or_load(key, hf_token="synthetic-token")

    with pytest.raises(RuntimeManagerError) as raised:
        manager.shutdown()

    assert raised.value.code is RuntimeManagerErrorCode.RUNTIME_CLEANUP_ERROR
    assert secret not in str(raised.value)
    assert str(private_path) not in str(raised.value)
    assert factory.adapters[0].release_calls == 1


def test_load_failure_with_release_failure_keeps_residual_for_shutdown(tmp_path):
    root = create_project_root(tmp_path / "project")
    release_secret = "synthetic-release-secret"
    workspaces: list[RuntimeWorkspace] = []
    events: list[str] = []
    factory = FakeAdapterFactory(
        events,
        [
            {
                "load_error": RuntimeError("synthetic load failure"),
                "release_error": RuntimeError(release_secret),
            }
        ],
    )
    manager = ModelManager(
        adapter_factory=factory,
        workspace_factory=_workspace_factory(root, workspaces),
    )
    key = _key(root)

    with pytest.raises(RuntimeManagerError) as raised:
        manager.get_or_load(key, hf_token="synthetic-token")

    assert raised.value.code is RuntimeManagerErrorCode.RUNTIME_LOAD_ERROR
    assert release_secret not in str(raised.value)
    assert release_secret not in raised.value.internal_detail
    assert manager.state is RuntimeState.FAILED
    assert manager.current_key == key
    assert manager.adapter is factory.adapters[0]
    assert not workspaces[0].working_directory.exists()


def test_load_failure_with_cleanup_failure_retries_cleanup_on_shutdown(tmp_path):
    root = create_project_root(tmp_path / "project")
    cleanup_secret = "synthetic-cleanup-secret"
    cleanup_calls: list[RuntimeWorkspace] = []
    workspaces: list[RuntimeWorkspace] = []
    events: list[str] = []
    factory = FakeAdapterFactory(
        events,
        [{"load_error": RuntimeError("synthetic load failure")}],
    )

    def cleanup(workspace: RuntimeWorkspace) -> None:
        cleanup_calls.append(workspace)
        if len(cleanup_calls) == 1:
            raise RuntimeError(cleanup_secret)
        cleanup_backend_workspace(workspace)

    manager = ModelManager(
        adapter_factory=factory,
        workspace_factory=_workspace_factory(root, workspaces),
        workspace_cleanup=cleanup,
    )
    key = _key(root)

    with pytest.raises(RuntimeManagerError) as raised:
        manager.get_or_load(key, hf_token="synthetic-token")

    assert raised.value.code is RuntimeManagerErrorCode.RUNTIME_LOAD_ERROR
    assert cleanup_secret not in str(raised.value)
    assert cleanup_secret not in raised.value.internal_detail
    assert manager.state is RuntimeState.FAILED
    assert manager.current_key == key
    assert manager.adapter is None
    assert len(cleanup_calls) == 1
    assert factory.adapters[0].release_calls == 1


def test_swap_removes_manager_strong_reference_to_previous_adapter(tmp_path):
    root = create_project_root(tmp_path / "project")
    manager, factory, _, _ = _manager(root)
    first = manager.get_or_load(_key(root, seed=42), hf_token="synthetic-token")
    reference = weakref.ref(first)
    del first
    manager.get_or_load(_key(root, seed=43), hf_token="synthetic-token")
    factory.adapters.pop(0)
    import gc
    gc.collect()
    assert reference() is None


@pytest.mark.parametrize("invalid_ttl", [math.nan, math.inf, True, -1])
def test_model_manager_rejects_invalid_ttl(invalid_ttl):
    with pytest.raises(ValueError):
        ModelManager(ttl_seconds=invalid_ttl)


def test_runtime_modules_do_not_import_real_generators():
    assert REAL_GENERATOR_MODULES.isdisjoint(sys.modules)
