from __future__ import annotations

import os
from pathlib import Path

import pytest

from interface.backend.adapters.base import AdapterError, AdapterErrorCode
from interface.backend.adapters.factory import create_adapter
from interface.backend.domain.capabilities import ApplicationMode
from interface.backend.tests.adapter_support import (
    DependencyRecorder,
    RecordingFactory,
    XIYAN_MODEL_ID,
    configuration,
    create_context_files,
    create_project_root,
)


def _xiyan_adapter(
    factory,
    dependencies,
    *,
    context="none",
    project_root,
):
    return create_adapter(
        configuration(
            library="xiyan_sql",
            context=context,
            model_id=XIYAN_MODEL_ID,
        ),
        ApplicationMode.BENCHMARK,
        random_seed=42,
        hf_token="synthetic-token",
        generator_factory=factory,
        database_config_resolver=dependencies.resolve_database,
        seed_setter=dependencies.set_seed,
        project_root=project_root,
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
def test_xiyan_context_modes_and_constructor_arguments(
    tmp_path, context, expects_doc, expects_examples
):
    create_context_files(tmp_path)
    factory = RecordingFactory()
    dependencies = DependencyRecorder()
    adapter = _xiyan_adapter(
        factory,
        dependencies,
        context=context,
        project_root=tmp_path,
    )

    adapter.load()

    kwargs = factory.calls[0]
    assert kwargs["local_model"] is True
    assert kwargs["model_id"] == XIYAN_MODEL_ID
    assert (kwargs["doc_path"] is not None) is expects_doc
    assert (kwargs["examples_path"] is not None) is expects_examples
    for key in ("doc_path", "examples_path"):
        if kwargs[key] is not None:
            assert Path(kwargs[key]).is_relative_to(tmp_path)


def test_xiyan_constructor_and_generation_observe_cn_then_restore_previous(
    monkeypatch, tmp_path
):
    create_project_root(tmp_path)
    monkeypatch.setenv("XIYAN_PROMPT_LANG", "en")
    factory = RecordingFactory()
    dependencies = DependencyRecorder()
    adapter = _xiyan_adapter(factory, dependencies, project_root=tmp_path)

    adapter.load()
    assert factory.prompt_languages == ["cn"]
    assert os.environ["XIYAN_PROMPT_LANG"] == "en"

    adapter.generate("pergunta sintética")
    assert factory.generator.prompt_languages == ["cn"]
    assert os.environ["XIYAN_PROMPT_LANG"] == "en"


def test_xiyan_removes_environment_when_originally_absent(monkeypatch, tmp_path):
    create_project_root(tmp_path)
    monkeypatch.delenv("XIYAN_PROMPT_LANG", raising=False)
    factory = RecordingFactory()
    dependencies = DependencyRecorder()
    adapter = _xiyan_adapter(factory, dependencies, project_root=tmp_path)

    adapter.load()
    assert "XIYAN_PROMPT_LANG" not in os.environ
    adapter.generate("pergunta sintética")
    assert "XIYAN_PROMPT_LANG" not in os.environ


def test_xiyan_restores_environment_after_constructor_failure(monkeypatch, tmp_path):
    create_project_root(tmp_path)
    monkeypatch.setenv("XIYAN_PROMPT_LANG", "previous")
    factory = RecordingFactory(constructor_error=RuntimeError("synthetic failure"))
    dependencies = DependencyRecorder()
    adapter = _xiyan_adapter(factory, dependencies, project_root=tmp_path)

    with pytest.raises(AdapterError) as raised:
        adapter.load()

    assert raised.value.code is AdapterErrorCode.ADAPTER_LOAD_ERROR
    assert os.environ["XIYAN_PROMPT_LANG"] == "previous"


def test_xiyan_restores_environment_after_generation_failure(monkeypatch, tmp_path):
    create_project_root(tmp_path)
    monkeypatch.setenv("XIYAN_PROMPT_LANG", "previous")
    factory = RecordingFactory(generation_error=RuntimeError("synthetic failure"))
    dependencies = DependencyRecorder()
    adapter = _xiyan_adapter(factory, dependencies, project_root=tmp_path)
    adapter.load()

    with pytest.raises(AdapterError) as raised:
        adapter.generate("pergunta sintética")

    assert raised.value.code is AdapterErrorCode.ADAPTER_GENERATION_ERROR
    assert os.environ["XIYAN_PROMPT_LANG"] == "previous"
