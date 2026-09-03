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


@pytest.mark.parametrize("mode", [ApplicationMode.CHAT, ApplicationMode.BENCHMARK])
@pytest.mark.parametrize(
    ("context", "seed", "expects_examples"),
    [
        ("default", 42, False),
        ("examples", 43, True),
    ],
)
def test_raw_model_context_passes_only_resolved_examples_and_seed(
    tmp_path, mode, context, seed, expects_examples
):
    if expects_examples:
        create_context_files(tmp_path)
    else:
        create_project_root(tmp_path)
    factory = RecordingFactory()
    dependencies = DependencyRecorder()
    adapter = create_adapter(
        configuration(context=context),
        mode,
        random_seed=seed,
        hf_token="synthetic-token",
        generator_factory=factory,
        database_config_resolver=dependencies.resolve_database,
        seed_setter=dependencies.set_seed,
        project_root=tmp_path,
    )

    adapter.load()

    kwargs = factory.calls[0]
    assert kwargs["examples_seed"] == seed
    assert (kwargs["examples_path"] is not None) is expects_examples
    if expects_examples:
        path = Path(kwargs["examples_path"])
        assert path.is_absolute()
        assert path.is_relative_to(tmp_path)
    assert dependencies.seed_calls == [seed]


def test_raw_model_chat_forwards_only_the_current_question(tmp_path):
    create_context_files(tmp_path)
    factory = RecordingFactory()
    dependencies = DependencyRecorder()
    adapter = create_adapter(
        configuration(context="examples"),
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


def test_raw_model_examples_missing_resource_is_structured_and_path_safe(tmp_path):
    create_project_root(tmp_path)

    with pytest.raises(AdapterError) as raised:
        create_adapter(
            configuration(context="examples"),
            ApplicationMode.CHAT,
            random_seed=42,
            hf_token=None,
            generator_factory=RecordingFactory(),
            project_root=tmp_path,
        )

    assert raised.value.code is AdapterErrorCode.CONTEXT_RESOURCE_NOT_FOUND
    assert str(tmp_path.resolve()) not in str(raised.value)
