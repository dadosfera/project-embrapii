from __future__ import annotations

import sys

import pytest

from interface.backend.adapters.base import AdapterError, AdapterErrorCode
from interface.backend.adapters.factory import create_adapter
from interface.backend.adapters.premsql_agent import PremSQLAdapter
from interface.backend.adapters.raw_model import RawModelAdapter
from interface.backend.adapters.vanna_ai import VannaAIAdapter
from interface.backend.adapters.xiyan_sql import XiYanSQLAdapter
from interface.backend.domain.capabilities import ApplicationMode
from interface.backend.tests.adapter_support import (
    DependencyRecorder,
    RecordingFactory,
    XIYAN_MODEL_ID,
    configuration,
    create_context_files,
    create_project_root,
)


REAL_GENERATOR_MODULES = {
    "src.rawmodel",
    "src.vannaai",
    "src.premsqlAgente",
    "src.xiyansql",
}


def test_importing_adapters_does_not_import_real_generators():
    assert REAL_GENERATOR_MODULES.isdisjoint(sys.modules)


@pytest.mark.parametrize(
    ("selected_configuration", "mode", "expected_type"),
    [
        (configuration(), ApplicationMode.CHAT, RawModelAdapter),
        (
            configuration(library="vanna_ai", context="none"),
            ApplicationMode.CHAT,
            VannaAIAdapter,
        ),
        (
            configuration(library="raw_model", context="examples"),
            ApplicationMode.CHAT,
            RawModelAdapter,
        ),
        (
            configuration(library="premsql_agent"),
            ApplicationMode.BENCHMARK,
            PremSQLAdapter,
        ),
        (
            configuration(
                library="xiyan_sql",
                context="none",
                model_id=XIYAN_MODEL_ID,
            ),
            ApplicationMode.BENCHMARK,
            XiYanSQLAdapter,
        ),
    ],
)
def test_factory_selects_only_catalogued_adapter(
    tmp_path, selected_configuration, mode, expected_type
):
    if selected_configuration.context == "examples":
        create_context_files(tmp_path)
    else:
        create_project_root(tmp_path)
    dependencies = DependencyRecorder()
    adapter = create_adapter(
        selected_configuration,
        mode,
        random_seed=42,
        hf_token="synthetic-token",
        generator_factory=RecordingFactory(),
        database_config_resolver=dependencies.resolve_database,
        seed_setter=dependencies.set_seed,
        project_root=tmp_path,
    )

    assert type(adapter) is expected_type


@pytest.mark.parametrize(
    "selected_configuration",
    [
        configuration(library="RawModel"),
        configuration(model_id="Qwen 2.5 Coder 7B Instruct"),
        configuration(library="xiyan_sql", context="none"),
        configuration(library="raw_model", context="documentation"),
    ],
)
def test_factory_rejects_labels_and_incompatible_combinations(
    tmp_path, selected_configuration
):
    with pytest.raises(AdapterError) as raised:
        create_adapter(
            selected_configuration,
            ApplicationMode.BENCHMARK,
            random_seed=42,
            hf_token=None,
            generator_factory=RecordingFactory(),
            project_root=tmp_path,
        )

    assert raised.value.code is AdapterErrorCode.UNSUPPORTED_COMBINATION


def test_factory_rejects_premsql_in_chat():
    with pytest.raises(AdapterError) as raised:
        create_adapter(
            configuration(library="premsql_agent"),
            ApplicationMode.CHAT,
            random_seed=42,
            hf_token=None,
            generator_factory=RecordingFactory(),
        )

    assert raised.value.code is AdapterErrorCode.UNSUPPORTED_COMBINATION
    assert str(raised.value) == (
        "PremSQLAgent não está disponível no Chat nesta versão. "
        "Use-o no modo Benchmark."
    )


def test_factory_accepts_premsql_in_benchmark(tmp_path):
    create_project_root(tmp_path)
    adapter = create_adapter(
        configuration(library="premsql_agent"),
        ApplicationMode.BENCHMARK,
        random_seed=42,
        hf_token=None,
        generator_factory=RecordingFactory(),
        project_root=tmp_path,
    )

    assert isinstance(adapter, PremSQLAdapter)


def test_factory_does_not_accept_arbitrary_mode():
    with pytest.raises(AdapterError) as raised:
        create_adapter(
            configuration(),
            "arbitrary-mode",
            random_seed=42,
            hf_token=None,
            generator_factory=RecordingFactory(),
        )

    assert raised.value.code is AdapterErrorCode.UNSUPPORTED_COMBINATION
