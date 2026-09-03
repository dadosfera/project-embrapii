from __future__ import annotations

import ast
from dataclasses import is_dataclass
from enum import Enum
import json
from pathlib import Path

import pytest

from interface.backend.domain.capabilities import (
    ApplicationMode,
    CapabilityErrorCode,
    ConfigurationSelection,
    ContextId,
    LibraryId,
    ModelFamily,
    get_initial_configuration,
    get_library_availability,
    list_contexts,
    list_contexts_for_library,
    list_databases,
    list_libraries,
    list_models,
    list_models_for_library,
    resolve_legacy_token,
    resolve_model_id,
    resolve_registry_name,
    serialize_catalog,
    validate_against_registry,
    validate_configuration,
)


EXPECTED_MODEL_PAIRS = (
    ("Qwen3-32B", "Qwen/Qwen3-32B"),
    ("Qwen2.5-Coder-32B-Instruct", "Qwen/Qwen2.5-Coder-32B-Instruct"),
    ("Qwen2.5-Coder-14B-Instruct", "Qwen/Qwen2.5-Coder-14B-Instruct"),
    ("Qwen2.5-Coder-7B-Instruct", "Qwen/Qwen2.5-Coder-7B-Instruct"),
    ("Llama-3.1-8B-Instruct", "meta-llama/Llama-3.1-8B-Instruct"),
    ("llama-3-sqlcoder-8b", "defog/llama-3-sqlcoder-8b"),
    (
        "XiYanSQL-QwenCoder-3B-2504",
        "XGenerationLab/XiYanSQL-QwenCoder-3B-2504",
    ),
    (
        "XiYanSQL-QwenCoder-7B-2504",
        "XGenerationLab/XiYanSQL-QwenCoder-7B-2504",
    ),
    (
        "XiYanSQL-QwenCoder-14B-2504",
        "XGenerationLab/XiYanSQL-QwenCoder-14B-2504",
    ),
    (
        "XiYanSQL-QwenCoder-32B-2504",
        "XGenerationLab/XiYanSQL-QwenCoder-32B-2504",
    ),
)

EXPECTED_MODEL_LABELS = (
    "Qwen 3 32B",
    "Qwen 2.5 Coder 32B Instruct",
    "Qwen 2.5 Coder 14B Instruct",
    "Qwen 2.5 Coder 7B Instruct",
    "Llama 3.1 8B Instruct",
    "Llama 3 SQLCoder 8B",
    "XiYanSQL QwenCoder 3B (2504)",
    "XiYanSQL QwenCoder 7B (2504)",
    "XiYanSQL QwenCoder 14B (2504)",
    "XiYanSQL QwenCoder 32B (2504)",
)


def _configuration(**changes: str) -> ConfigurationSelection:
    values = {
        "database": "sih_database",
        "library": "raw_model",
        "model_id": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "context": "default",
    }
    values.update(changes)
    return ConfigurationSelection(**values)


def _load_registry_resolver_without_importing_src():
    registry_path = Path(__file__).resolve().parents[3] / "src" / "utilitis.py"
    tree = ast.parse(registry_path.read_text(encoding="utf-8"), filename=str(registry_path))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "get_model_id"
    )
    isolated_module = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(isolated_module)
    namespace: dict[str, object] = {}
    exec(compile(isolated_module, str(registry_path), "exec"), namespace)
    return namespace["get_model_id"]


def test_catalog_has_exact_v1_cardinalities():
    assert len(list_databases()) == 2
    assert len(list_libraries()) == 4
    assert len(list_models()) == 10
    assert len(list_contexts()) == 5


def test_catalog_has_exact_visible_metadata():
    assert [
        (item.id.value, item.label, item.engine.value) for item in list_databases()
    ] == [
        ("sih_database", "SIH/DataSUS", "postgresql"),
        ("datasus", "JABUTI-SQL", "postgresql"),
    ]
    assert [item.label for item in list_libraries()] == [
        "RawModel",
        "VannaAI",
        "PremSQLAgent",
        "XiYanSQL",
    ]
    assert tuple(item.label for item in list_models()) == EXPECTED_MODEL_LABELS
    assert [item.label for item in list_contexts()] == [
        "Configuração padrão",
        "Sem contexto",
        "Somente documentação",
        "Somente exemplos",
        "Documentação e exemplos",
    ]


def test_catalog_identifiers_labels_and_registry_names_are_unique():
    databases = list_databases()
    libraries = list_libraries()
    models = list_models()
    contexts = list_contexts()

    for values in (
        [item.id.value for item in databases],
        [item.label for item in databases],
        [item.id.value for item in libraries],
        [item.label for item in libraries],
        [item.id for item in models],
        [item.label for item in models],
        [item.registry_name for item in models],
        [item.id.value for item in contexts],
        [item.label for item in contexts],
    ):
        assert len(values) == len(set(values))


def test_lists_have_stable_specified_order():
    assert [item.id.value for item in list_databases()] == ["sih_database", "datasus"]
    assert [item.id.value for item in list_libraries()] == [
        "raw_model",
        "vanna_ai",
        "premsql_agent",
        "xiyan_sql",
    ]
    assert [item.registry_name for item in list_models()] == [
        pair[0] for pair in EXPECTED_MODEL_PAIRS
    ]
    assert [item.id.value for item in list_contexts()] == [
        "default",
        "none",
        "documentation",
        "examples",
        "documentation_and_examples",
    ]
    for entries in (
        list_databases(),
        list_libraries(),
        list_models(),
        list_contexts(),
    ):
        assert [item.order for item in entries] == list(range(1, len(entries) + 1))


def test_all_registry_names_resolve_to_expected_ids_in_both_directions():
    for registry_name, model_id in EXPECTED_MODEL_PAIRS:
        assert resolve_model_id(registry_name).value == model_id
        assert resolve_registry_name(model_id).value == registry_name


def test_catalog_matches_current_registry_without_importing_src_module():
    resolver = _load_registry_resolver_without_importing_src()

    result = validate_against_registry(resolver)

    assert result.valid
    assert result.issues == ()


@pytest.mark.parametrize(
    ("library_id", "expected_family"),
    [
        (LibraryId.RAW_MODEL.value, ModelFamily.GENERAL),
        (LibraryId.VANNA_AI.value, ModelFamily.GENERAL),
        (LibraryId.PREMSQL_AGENT.value, ModelFamily.GENERAL),
        (LibraryId.XIYAN_SQL.value, ModelFamily.XIYAN),
    ],
)
def test_library_lists_only_compatible_model_family(library_id, expected_family):
    result = list_models_for_library(library_id)

    assert result.is_valid
    assert result.value
    assert {model.family for model in result.value} == {expected_family}


def test_general_model_is_rejected_by_xiyan_and_xiyan_is_rejected_elsewhere():
    general_for_xiyan = validate_configuration(
        _configuration(library="xiyan_sql", context="none")
    )
    xiyan_for_raw = validate_configuration(
        _configuration(model_id=EXPECTED_MODEL_PAIRS[6][1])
    )

    assert general_for_xiyan.error.code is CapabilityErrorCode.UNSUPPORTED_COMBINATION
    assert xiyan_for_raw.error.code is CapabilityErrorCode.UNSUPPORTED_COMBINATION


def test_premsql_availability_is_mode_specific_and_structured():
    chat = get_library_availability("premsql_agent", ApplicationMode.CHAT)
    benchmark = get_library_availability("premsql_agent", ApplicationMode.BENCHMARK)

    assert chat.value is not None and not chat.value.available
    assert chat.value.reason is not None
    assert chat.value.reason.message == (
        "PremSQLAgent não está disponível no Chat nesta versão. "
        "Use-o no modo Benchmark."
    )
    assert benchmark.value is not None and benchmark.value.available
    assert benchmark.value.reason is None


@pytest.mark.parametrize(
    ("library_id", "expected_contexts"),
    [
        ("raw_model", ("default", "examples")),
        ("premsql_agent", ("default",)),
        (
            "vanna_ai",
            ("none", "documentation", "examples", "documentation_and_examples"),
        ),
        (
            "xiyan_sql",
            ("none", "documentation", "examples", "documentation_and_examples"),
        ),
    ],
)
def test_library_contexts_are_exact(library_id, expected_contexts):
    result = list_contexts_for_library(library_id)

    assert tuple(context.id.value for context in result.value) == expected_contexts


@pytest.mark.parametrize(
    ("library_id", "context_id", "expected_token"),
    [
        ("raw_model", "default", "rawModel"),
        ("raw_model", "examples", "rawModel_exemplos"),
        ("premsql_agent", "default", "PremSQLAgente"),
        ("vanna_ai", "none", "vannaAi"),
        ("vanna_ai", "documentation", "vannaAi_contexto"),
        ("vanna_ai", "examples", "vannaAi_exemplos"),
        (
            "vanna_ai",
            "documentation_and_examples",
            "vannaAi_contexto_exemplos",
        ),
        ("xiyan_sql", "none", "XiYanSQL"),
        ("xiyan_sql", "documentation", "XiYanSQL_contexto"),
        ("xiyan_sql", "examples", "XiYanSQL_exemplos"),
        (
            "xiyan_sql",
            "documentation_and_examples",
            "XiYanSQL_contexto_exemplos",
        ),
    ],
)
def test_all_legacy_tokens(library_id, context_id, expected_token):
    assert resolve_legacy_token(library_id, context_id).value == expected_token


def test_xiyan_prompt_language_is_fixed_and_not_a_context():
    xiyan = next(item for item in list_libraries() if item.id is LibraryId.XIYAN_SQL)

    assert xiyan.prompt_language == "cn"
    assert "cn" not in [context.id.value for context in list_contexts()]


def test_initial_configuration_is_exact_and_valid():
    configuration = get_initial_configuration()

    assert configuration == _configuration()
    assert validate_configuration(configuration).is_valid
    assert validate_configuration(configuration, ApplicationMode.CHAT).is_valid
    assert validate_configuration(configuration, ApplicationMode.BENCHMARK).is_valid


@pytest.mark.parametrize(
    ("configuration", "expected_code"),
    [
        (_configuration(database="unknown"), CapabilityErrorCode.UNKNOWN_DATABASE),
        (_configuration(library="unknown"), CapabilityErrorCode.UNKNOWN_LIBRARY),
        (_configuration(model_id="unknown"), CapabilityErrorCode.UNKNOWN_MODEL),
        (_configuration(context="unknown"), CapabilityErrorCode.UNKNOWN_CONTEXT),
        (
            _configuration(library="raw_model", context="none"),
            CapabilityErrorCode.UNSUPPORTED_COMBINATION,
        ),
    ],
)
def test_invalid_configurations_return_structured_errors(configuration, expected_code):
    result = validate_configuration(configuration)

    assert not result.is_valid
    assert result.value is None
    assert result.error is not None
    assert result.error.code is expected_code


def test_premsql_configuration_is_rejected_in_chat_and_valid_in_benchmark():
    configuration = _configuration(library="premsql_agent")

    chat = validate_configuration(configuration, ApplicationMode.CHAT)
    benchmark = validate_configuration(configuration, ApplicationMode.BENCHMARK)

    assert chat.error.code is CapabilityErrorCode.UNSUPPORTED_COMBINATION
    assert benchmark.is_valid


def test_labels_are_not_accepted_as_model_identifiers():
    result = validate_configuration(
        _configuration(model_id="Qwen 2.5 Coder 7B Instruct")
    )

    assert result.error.code is CapabilityErrorCode.UNKNOWN_MODEL


def test_serialized_catalog_contains_only_json_compatible_values():
    serialized = serialize_catalog()

    def assert_plain(value):
        assert not isinstance(value, Enum)
        assert not is_dataclass(value)
        if isinstance(value, dict):
            for key, item in value.items():
                assert isinstance(key, str)
                assert_plain(item)
        elif isinstance(value, list):
            for item in value:
                assert_plain(item)
        else:
            assert value is None or isinstance(value, (str, int, float, bool))

    assert_plain(serialized)
    json.dumps(serialized, ensure_ascii=False)
