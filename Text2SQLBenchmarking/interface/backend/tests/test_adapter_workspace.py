from __future__ import annotations

import os
from pathlib import Path

import pytest

from interface.backend.adapters.base import AdapterError, AdapterErrorCode
from interface.backend.adapters.factory import create_adapter
from interface.backend.adapters.workspace import (
    RuntimeWorkspace,
    WorkspaceLifecycleOwner,
)
from interface.backend.domain.capabilities import ApplicationMode
from interface.backend.tests.adapter_support import (
    DependencyRecorder,
    FakeGenerator,
    RecordingFactory,
    XIYAN_MODEL_ID,
    configuration,
    create_project_root,
)


def _raw_adapter(project_root: Path, runtime_directory: Path, factory):
    dependencies = DependencyRecorder()
    return create_adapter(
        configuration(),
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token=None,
        generator_factory=factory,
        database_config_resolver=dependencies.resolve_database,
        seed_setter=dependencies.set_seed,
        project_root=project_root,
        runtime_directory=runtime_directory,
    )


def _runtime_directory(project_root: Path, identifier: str = "injected") -> Path:
    return project_root / "interface" / ".runtime" / "adapters" / identifier


def test_constructor_and_generate_run_in_workspace_and_restore_cwd(tmp_path):
    root = create_project_root(tmp_path / "project")
    runtime = _runtime_directory(root)
    factory = RecordingFactory()
    previous = Path.cwd()
    adapter = _raw_adapter(root, runtime, factory)

    adapter.load()
    assert factory.constructor_directories == [runtime.resolve()]
    assert Path.cwd() == previous

    adapter.generate("pergunta sintética")
    assert factory.generator.generation_directories == [runtime.resolve()]
    assert Path.cwd() == previous


def test_cwd_is_restored_after_constructor_failure(tmp_path):
    root = create_project_root(tmp_path / "project")
    runtime = _runtime_directory(root)
    factory = RecordingFactory(constructor_error=RuntimeError("synthetic"))
    previous = Path.cwd()
    adapter = _raw_adapter(root, runtime, factory)

    with pytest.raises(AdapterError) as raised:
        adapter.load()

    assert raised.value.code is AdapterErrorCode.ADAPTER_LOAD_ERROR
    assert factory.constructor_directories == [runtime.resolve()]
    assert Path.cwd() == previous


def test_cwd_is_restored_after_generation_failure(tmp_path):
    root = create_project_root(tmp_path / "project")
    runtime = _runtime_directory(root)
    factory = RecordingFactory(generation_error=RuntimeError("synthetic"))
    previous = Path.cwd()
    adapter = _raw_adapter(root, runtime, factory)
    adapter.load()

    with pytest.raises(AdapterError) as raised:
        adapter.generate("pergunta sintética")

    assert raised.value.code is AdapterErrorCode.ADAPTER_GENERATION_ERROR
    assert factory.generator.generation_directories == [runtime.resolve()]
    assert Path.cwd() == previous


def test_xiyan_combines_workspace_and_language_and_restores_both(
    tmp_path, monkeypatch
):
    root = create_project_root(tmp_path / "project")
    runtime = _runtime_directory(root)
    factory = RecordingFactory(generation_error=RuntimeError("synthetic"))
    dependencies = DependencyRecorder()
    previous_cwd = Path.cwd()
    monkeypatch.setenv("XIYAN_PROMPT_LANG", "previous")
    adapter = create_adapter(
        configuration(
            library="xiyan_sql",
            context="none",
            model_id=XIYAN_MODEL_ID,
        ),
        ApplicationMode.BENCHMARK,
        random_seed=42,
        hf_token=None,
        generator_factory=factory,
        database_config_resolver=dependencies.resolve_database,
        seed_setter=dependencies.set_seed,
        project_root=root,
        runtime_directory=runtime,
    )

    adapter.load()
    assert factory.constructor_directories == [runtime.resolve()]
    assert factory.prompt_languages == ["cn"]
    assert Path.cwd() == previous_cwd
    assert os.environ["XIYAN_PROMPT_LANG"] == "previous"

    with pytest.raises(AdapterError) as raised:
        adapter.generate("pergunta sintética")

    assert raised.value.code is AdapterErrorCode.ADAPTER_GENERATION_ERROR
    assert factory.generator.generation_directories == [runtime.resolve()]
    assert factory.generator.prompt_languages == ["cn"]
    assert Path.cwd() == previous_cwd
    assert os.environ["XIYAN_PROMPT_LANG"] == "previous"


def test_workspace_links_synthetic_cache_without_copying_or_modifying_it(tmp_path):
    root = create_project_root(tmp_path / "project")
    cache = root / "local_models"
    marker = cache / "synthetic-model.marker"
    marker.write_text("conteúdo sintético imutável", encoding="utf-8")
    before = marker.stat()
    workspace = RuntimeWorkspace.create(
        project_root=root,
        runtime_directory=_runtime_directory(root),
    )

    link = workspace.working_directory / "local_models"
    assert link.is_symlink()
    assert link.resolve(strict=True) == cache.resolve(strict=True)
    assert (link / marker.name).samefile(marker)
    assert marker.read_text(encoding="utf-8") == "conteúdo sintético imutável"
    after = marker.stat()
    assert after.st_size == before.st_size
    assert after.st_mtime_ns == before.st_mtime_ns
    assert sorted(path.name for path in cache.iterdir()) == [marker.name]


@pytest.mark.parametrize(
    ("library", "mode", "context", "state_directory"),
    [
        ("vanna_ai", ApplicationMode.CHAT, "none", "vanna_storage"),
        ("premsql_agent", ApplicationMode.BENCHMARK, "default", "premsql"),
    ],
)
def test_mutable_legacy_state_stays_inside_workspace(
    tmp_path, library, mode, context, state_directory
):
    root = create_project_root(tmp_path / "project")
    runtime = _runtime_directory(root)
    dependencies = DependencyRecorder()

    def state_creating_factory(**kwargs):
        Path(state_directory).mkdir()
        return FakeGenerator()

    adapter = create_adapter(
        configuration(library=library, context=context),
        mode,
        random_seed=42,
        hf_token=None,
        generator_factory=state_creating_factory,
        database_config_resolver=dependencies.resolve_database,
        seed_setter=dependencies.set_seed,
        project_root=root,
        runtime_directory=runtime,
    )
    adapter.load()

    isolated_state = runtime / state_directory
    assert isolated_state.is_dir()
    assert not isolated_state.is_symlink()
    assert not (root / state_directory).exists()


def test_existing_local_models_link_to_wrong_target_is_rejected(tmp_path):
    root = create_project_root(tmp_path / "project")
    runtime = _runtime_directory(root)
    wrong_target = tmp_path / "other-cache"
    runtime.mkdir(parents=True)
    wrong_target.mkdir()
    (runtime / "local_models").symlink_to(wrong_target, target_is_directory=True)

    with pytest.raises(AdapterError) as raised:
        RuntimeWorkspace.create(project_root=root, runtime_directory=runtime)

    assert raised.value.code is AdapterErrorCode.RUNTIME_WORKSPACE_ERROR
    assert str(wrong_target.resolve()) not in str(raised.value)


def test_missing_model_cache_is_a_path_safe_workspace_error(tmp_path):
    root = tmp_path / "project-without-cache"
    root.mkdir()

    with pytest.raises(AdapterError) as raised:
        RuntimeWorkspace.create(
            project_root=root,
            runtime_directory=_runtime_directory(root),
        )

    assert raised.value.code is AdapterErrorCode.RUNTIME_WORKSPACE_ERROR
    assert str(root.resolve()) not in str(raised.value)


def test_workspace_ownership_distinguishes_unique_and_injected_directory(tmp_path):
    root = create_project_root(tmp_path / "project")
    automatic = RuntimeWorkspace.create(project_root=root)
    injected_directory = _runtime_directory(root, "caller-provided")
    injected = RuntimeWorkspace.create(
        project_root=root,
        runtime_directory=injected_directory,
    )

    assert automatic.lifecycle_owner is WorkspaceLifecycleOwner.BACKEND
    assert automatic.working_directory.parent == (
        root / "interface" / ".runtime" / "adapters"
    ).resolve()
    assert automatic.working_directory != injected.working_directory
    assert injected.lifecycle_owner is WorkspaceLifecycleOwner.CALLER
    assert injected.working_directory == injected_directory.resolve()


def test_factory_accepts_an_injected_workspace_dependency(tmp_path):
    root = create_project_root(tmp_path / "project")
    workspace = RuntimeWorkspace.create(
        project_root=root,
        runtime_directory=_runtime_directory(root),
    )
    factory = RecordingFactory()
    dependencies = DependencyRecorder()

    adapter = create_adapter(
        configuration(),
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token=None,
        generator_factory=factory,
        database_config_resolver=dependencies.resolve_database,
        seed_setter=dependencies.set_seed,
        workspace=workspace,
    )

    assert adapter.workspace is workspace


def test_release_hook_failure_restores_cwd_and_removes_loaded_state(
    tmp_path, monkeypatch
):
    root = create_project_root(tmp_path / "project")
    runtime = _runtime_directory(root)
    factory = RecordingFactory()
    adapter = _raw_adapter(root, runtime, factory)
    adapter.load()
    generator = factory.generator
    observed_directories: list[Path] = []
    previous = Path.cwd()

    def failing_release(current_generator):
        observed_directories.append(Path.cwd())
        assert current_generator is generator
        raise RuntimeError("synthetic release failure")

    monkeypatch.setattr(adapter, "_release_generator", failing_release)
    with pytest.raises(AdapterError) as raised:
        adapter.release()

    assert raised.value.code is AdapterErrorCode.ADAPTER_RELEASE_ERROR
    assert observed_directories == [runtime.resolve()]
    assert Path.cwd() == previous
    assert not adapter.is_loaded
    assert adapter._generator is None

    successful_directories: list[Path] = []

    def successful_release(current_generator):
        successful_directories.append(Path.cwd())
        assert current_generator is generator

    monkeypatch.setattr(adapter, "_release_generator", successful_release)
    adapter.release()
    adapter.release()
    assert successful_directories == []
    assert Path.cwd() == previous
    assert not adapter.is_loaded


def test_factory_uses_an_explicit_falsey_injected_factory(tmp_path):
    root = create_project_root(tmp_path / "project")

    class FalseyFactory(RecordingFactory):
        def __bool__(self):
            return False

    factory = FalseyFactory()
    adapter = _raw_adapter(root, _runtime_directory(root), factory)
    adapter.load()

    assert len(factory.calls) == 1
