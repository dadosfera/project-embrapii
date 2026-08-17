from __future__ import annotations

from dataclasses import replace
import json
import math

import pytest

from interface.backend.domain.capabilities import ApplicationMode
from interface.backend.runtime.key import (
    DEFAULT_VANNA_MAX_NEW_TOKENS,
    GenerationParameters,
    RuntimeKey,
    RuntimeKeyError,
)
from interface.backend.tests.adapter_support import (
    XIYAN_MODEL_ID,
    configuration,
    create_context_files,
    create_project_root,
)


def _key(tmp_path, **overrides) -> RuntimeKey:
    root = create_project_root(tmp_path / "project")
    return RuntimeKey.from_configuration(
        configuration(**overrides),
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token="synthetic-secret-token",
        project_root=root,
    )


def test_equal_runtime_keys_are_hashable_and_equal(tmp_path):
    first = _key(tmp_path)
    second = _key(tmp_path)

    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second}) == 1


def test_methodological_fields_change_the_runtime_key(tmp_path):
    key = _key(tmp_path)
    variants = (
        replace(key, random_seed=43),
        replace(key, documentation_fingerprint="different-documentation"),
        replace(key, examples_fingerprint="different-examples"),
        replace(key, token_fingerprint="sha256:" + "0" * 64),
        replace(key, mode=ApplicationMode.BENCHMARK),
    )

    assert all(variant != key for variant in variants)


def test_key_never_exposes_raw_token_in_repr_or_serialization(tmp_path):
    secret = "synthetic-secret-token"
    key = _key(tmp_path)
    serialized = key.as_dict()

    assert secret not in repr(key)
    assert secret not in json.dumps(serialized, sort_keys=True)
    assert serialized["token_fingerprint"].startswith("sha256:")


def test_context_file_fingerprint_changes_when_server_resource_changes(tmp_path):
    root = tmp_path / "project"
    create_context_files(root)
    selection = configuration(library="vanna_ai", context="documentation")
    first = RuntimeKey.from_configuration(
        selection,
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token=None,
        project_root=root,
    )
    documentation = root / "datasets" / "sih_database" / "sih_documentation_resumida.md"
    documentation.write_text("conteúdo sintético alterado", encoding="utf-8")
    second = RuntimeKey.from_configuration(
        selection,
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token=None,
        project_root=root,
    )

    assert first.documentation_fingerprint != second.documentation_fingerprint
    assert first.examples_fingerprint is None


def test_raw_examples_context_has_distinct_token_seed_and_file_fingerprint(tmp_path):
    root = tmp_path / "project"
    create_context_files(root)
    default = RuntimeKey.from_configuration(
        configuration(),
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token=None,
        project_root=root,
    )
    selected = configuration(context="examples")
    first = RuntimeKey.from_configuration(
        selected,
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token=None,
        project_root=root,
    )
    examples = root / "datasets" / "sih_database" / "exemplos.json"
    examples.write_text('[{"question":"q","sql":"SELECT 1"}]', encoding="utf-8")
    changed_file = RuntimeKey.from_configuration(
        selected,
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token=None,
        project_root=root,
    )
    changed_seed = RuntimeKey.from_configuration(
        selected,
        ApplicationMode.CHAT,
        random_seed=43,
        hf_token=None,
        project_root=root,
    )

    assert default.legacy_token == "rawModel"
    assert default.examples_fingerprint is None
    assert first.legacy_token == "rawModel_exemplos"
    assert first.examples_fingerprint is not None
    assert first != default
    assert changed_file.examples_fingerprint != first.examples_fingerprint
    assert changed_seed != changed_file


def test_xiyan_key_fixes_cn_and_accepts_explicit_effective_parameters(tmp_path):
    root = create_project_root(tmp_path / "project")
    parameters = GenerationParameters(
        max_new_tokens=1024,
        do_sample=True,
        temperature=0.1,
        top_p=0.8,
    )
    key = RuntimeKey.from_configuration(
        configuration(
            library="xiyan_sql",
            context="none",
            model_id=XIYAN_MODEL_ID,
        ),
        ApplicationMode.BENCHMARK,
        random_seed=42,
        hf_token=None,
        generation_parameters=parameters,
        project_root=root,
    )

    assert key.xiyan_prompt_language == "cn"
    assert key.generation_parameters == parameters


def test_vanna_key_uses_the_effective_server_generation_limit(tmp_path, monkeypatch):
    root = create_project_root(tmp_path / "project")
    monkeypatch.setenv("VANNA_MAX_NEW_TOKENS", "777")

    key = RuntimeKey.from_configuration(
        configuration(library="vanna_ai", context="none"),
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token=None,
        project_root=root,
    )

    assert key.generation_parameters.max_new_tokens == 777


def test_vanna_key_uses_the_canonical_default_without_environment(tmp_path, monkeypatch):
    root = create_project_root(tmp_path / "project")
    monkeypatch.delenv("VANNA_MAX_NEW_TOKENS", raising=False)

    key = RuntimeKey.from_configuration(
        configuration(library="vanna_ai", context="none"),
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token=None,
        project_root=root,
    )

    assert key.generation_parameters.max_new_tokens == DEFAULT_VANNA_MAX_NEW_TOKENS
    assert DEFAULT_VANNA_MAX_NEW_TOKENS == 4096


@pytest.mark.parametrize("invalid_seed", [None, True, "42", 42.0])
def test_runtime_key_requires_an_integer_seed(tmp_path, invalid_seed):
    root = create_project_root(tmp_path / "project")

    with pytest.raises(RuntimeKeyError):
        RuntimeKey.from_configuration(
            configuration(),
            ApplicationMode.CHAT,
            random_seed=invalid_seed,
            hf_token=None,
            project_root=root,
        )


def test_runtime_key_rejects_arbitrary_generation_parameter_override(tmp_path):
    root = create_project_root(tmp_path / "project")
    override = GenerationParameters(max_new_tokens=999, do_sample=False)

    with pytest.raises(RuntimeKeyError):
        RuntimeKey.from_configuration(
            configuration(),
            ApplicationMode.CHAT,
            random_seed=42,
            hf_token=None,
            generation_parameters=override,
            project_root=root,
        )


@pytest.mark.parametrize("invalid_do_sample", [0, 1, "true"])
def test_generation_parameters_reject_invalid_do_sample(invalid_do_sample):
    with pytest.raises(RuntimeKeyError):
        GenerationParameters(do_sample=invalid_do_sample).validate()


@pytest.mark.parametrize("invalid_temperature", [-0.1, math.nan, math.inf])
def test_generation_parameters_reject_invalid_temperature(invalid_temperature):
    with pytest.raises(RuntimeKeyError):
        GenerationParameters(temperature=invalid_temperature).validate()


@pytest.mark.parametrize("invalid_top_p", [0, 1.1, math.nan, math.inf])
def test_generation_parameters_reject_invalid_top_p(invalid_top_p):
    with pytest.raises(RuntimeKeyError):
        GenerationParameters(top_p=invalid_top_p).validate()
