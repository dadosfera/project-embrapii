from __future__ import annotations

from pathlib import Path

import pytest

from interface.backend.adapters.base import AdapterError, AdapterErrorCode
from interface.backend.adapters.factory import create_adapter
from interface.backend.domain.capabilities import ApplicationMode
from interface.backend.tests.adapter_support import (
    DependencyRecorder,
    RecordingFactory,
    configuration,
    create_context_files,
    create_project_root,
)


@pytest.mark.parametrize(
    ("context", "expects_doc", "expects_examples"),
    [
        ("none", False, False),
        ("documentation", True, False),
        ("examples", False, True),
        ("documentation_and_examples", True, True),
    ],
)
def test_vanna_context_modes_use_only_server_resolved_paths(
    tmp_path, context, expects_doc, expects_examples
):
    create_context_files(tmp_path)
    factory = RecordingFactory()
    dependencies = DependencyRecorder()
    adapter = create_adapter(
        configuration(library="vanna_ai", context=context),
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token="synthetic-token",
        generator_factory=factory,
        database_config_resolver=dependencies.resolve_database,
        seed_setter=dependencies.set_seed,
        project_root=tmp_path,
    )

    adapter.load()

    kwargs = factory.calls[0]
    assert kwargs["local_model"] is True
    assert kwargs["model_id"] == "Qwen/Qwen2.5-Coder-7B-Instruct"
    assert (kwargs["doc_path"] is not None) is expects_doc
    assert (kwargs["examples_path"] is not None) is expects_examples
    for key in ("doc_path", "examples_path"):
        if kwargs[key] is not None:
            path = Path(kwargs[key])
            assert path.is_absolute()
            assert path.is_relative_to(tmp_path)


def test_vanna_missing_context_resource_is_structured_and_path_safe(tmp_path):
    create_project_root(tmp_path)
    expected_path = tmp_path / "datasets" / "sih_database"

    with pytest.raises(AdapterError) as raised:
        create_adapter(
            configuration(library="vanna_ai", context="documentation"),
            ApplicationMode.CHAT,
            random_seed=42,
            hf_token=None,
            generator_factory=RecordingFactory(),
            project_root=tmp_path,
        )

    assert raised.value.code is AdapterErrorCode.CONTEXT_RESOURCE_NOT_FOUND
    assert str(expected_path.resolve()) not in str(raised.value)


def test_vanna_generate_forwards_question_without_history(tmp_path):
    create_project_root(tmp_path)
    factory = RecordingFactory()
    dependencies = DependencyRecorder()
    adapter = create_adapter(
        configuration(library="vanna_ai", context="none"),
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token=None,
        generator_factory=factory,
        database_config_resolver=dependencies.resolve_database,
        seed_setter=dependencies.set_seed,
        project_root=tmp_path,
    )
    adapter.load()

    adapter.generate("somente esta pergunta")

    assert factory.generator.questions == ["somente esta pergunta"]
