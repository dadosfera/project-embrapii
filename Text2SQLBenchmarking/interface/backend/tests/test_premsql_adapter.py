from __future__ import annotations

from interface.backend.adapters.factory import create_adapter
from interface.backend.domain.capabilities import ApplicationMode, LibraryId
from interface.backend.tests.adapter_support import (
    DependencyRecorder,
    RecordingFactory,
    configuration,
    create_project_root,
)


def test_premsql_benchmark_preserves_constructor_and_declares_sql_execution(tmp_path):
    create_project_root(tmp_path)
    factory = RecordingFactory()
    dependencies = DependencyRecorder()
    selected_configuration = configuration(library="premsql_agent")
    adapter = create_adapter(
        selected_configuration,
        ApplicationMode.BENCHMARK,
        random_seed=42,
        hf_token="synthetic-token",
        generator_factory=factory,
        database_config_resolver=dependencies.resolve_database,
        seed_setter=dependencies.set_seed,
        project_root=tmp_path,
    )

    adapter.load()
    result = adapter.generate("pergunta sintética")

    assert factory.calls == [
        {
            "db_config": dependencies.db_config,
            "model_id": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "hf_token": "synthetic-token",
            "local_model": True,
        }
    ]
    assert result.library is LibraryId.PREMSQL_AGENT
    assert result.behavior.generation_may_execute_sql
    assert factory.generator.questions == ["pergunta sintética"]


def test_premsql_release_is_idempotent(tmp_path):
    create_project_root(tmp_path)
    dependencies = DependencyRecorder()
    adapter = create_adapter(
        configuration(library="premsql_agent"),
        ApplicationMode.BENCHMARK,
        random_seed=42,
        hf_token=None,
        generator_factory=RecordingFactory(),
        database_config_resolver=dependencies.resolve_database,
        seed_setter=dependencies.set_seed,
        project_root=tmp_path,
    )
    adapter.load()

    adapter.release()
    adapter.release()

    assert not adapter.is_loaded
