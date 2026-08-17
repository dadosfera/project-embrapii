from __future__ import annotations

import json
import random
import sys

import pytest

import src.rawmodel as rawmodel_module
from src.utilitis import get_examples_path


# A factory dos adapters deve continuar importando o gerador apenas em load().
sys.modules.pop("src.rawmodel", None)


def _model(examples=None) -> rawmodel_module.RawModel:
    model = object.__new__(rawmodel_module.RawModel)
    model.few_shot_examples = list(examples or [])
    return model


def _write_examples(tmp_path, examples) -> str:
    path = tmp_path / "examples.json"
    path.write_text(json.dumps(examples), encoding="utf-8")
    return str(path)


def _examples(amount: int) -> list[dict[str, str]]:
    return [
        {"question": f"pergunta {index}", "sql": f"SELECT {index}"}
        for index in range(amount)
    ]


def test_default_prompt_remains_system_followed_by_current_question():
    messages = _model()._build_prompt("CREATE TABLE t (id INT);", "pergunta atual")

    assert [message["role"] for message in messages] == ["system", "user"]
    assert messages[-1] == {"role": "user", "content": "pergunta atual"}
    assert messages[0]["content"] == (
        "You are an expert SQL assistant. "
        "Given the database schema below, write a single valid SQL query "
        "that answers the user's question. "
        "Return ONLY the SQL query, without explanations or markdown.\n\n"
        "### Schema\nCREATE TABLE t (id INT);"
    )


def test_few_shot_pairs_stay_between_system_and_current_question():
    selected = [
        {"question": "exemplo um", "sql": "SELECT 1"},
        {"question": "exemplo dois", "sql": "SELECT 2"},
    ]

    messages = _model(selected)._build_prompt("schema", "pergunta atual")

    assert messages[1:] == [
        {"role": "user", "content": "exemplo um"},
        {"role": "assistant", "content": "SELECT 1"},
        {"role": "user", "content": "exemplo dois"},
        {"role": "assistant", "content": "SELECT 2"},
        {"role": "user", "content": "pergunta atual"},
    ]


def test_examples_deduplicate_stripped_sql_and_preserve_first_occurrence(tmp_path):
    path = _write_examples(
        tmp_path,
        [
            {"question": "primeira", "sql": "SELECT 1"},
            {"question": "duplicada", "sql": " SELECT 1 "},
            {"question": "segunda", "sql": "SELECT 2"},
            {"question": "terceira", "sql": "SELECT 3"},
        ],
    )

    selected = rawmodel_module.RawModel._load_examples(path, 42)

    assert len(selected) == 3
    assert {item["sql"].strip() for item in selected} == {
        "SELECT 1",
        "SELECT 2",
        "SELECT 3",
    }
    assert "primeira" in {item["question"] for item in selected}
    assert "duplicada" not in {item["question"] for item in selected}


def test_examples_select_at_most_three_and_use_all_available_candidates(tmp_path):
    many_path = _write_examples(tmp_path, _examples(8))
    assert len(rawmodel_module.RawModel._load_examples(many_path, 42)) == 3

    few_path = tmp_path / "few.json"
    few_path.write_text(json.dumps(_examples(2)), encoding="utf-8")
    selected = rawmodel_module.RawModel._load_examples(str(few_path), 42)
    assert {item["sql"] for item in selected} == {"SELECT 0", "SELECT 1"}


def test_example_selection_is_deterministic_seeded_and_does_not_change_source(tmp_path):
    path = tmp_path / "examples.json"
    source = json.dumps(_examples(8), ensure_ascii=False, indent=2)
    path.write_text(source, encoding="utf-8")

    first = rawmodel_module.RawModel._load_examples(str(path), 42)
    repeated = rawmodel_module.RawModel._load_examples(str(path), 42)
    other_seed = rawmodel_module.RawModel._load_examples(str(path), 43)

    assert first == repeated
    assert first != other_seed
    assert path.read_text(encoding="utf-8") == source


def test_example_selection_does_not_modify_global_random_state(tmp_path):
    path = _write_examples(tmp_path, _examples(8))
    previous_state = random.getstate()
    try:
        random.seed(2026)
        expected = [random.random() for _ in range(4)]
        random.seed(2026)

        rawmodel_module.RawModel._load_examples(path, 42)
        actual = [random.random() for _ in range(4)]

        assert actual == expected
    finally:
        random.setstate(previous_state)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        ["não é objeto"],
        [{"sql": "SELECT 1"}],
        [{"question": "pergunta"}],
        [{"question": 1, "sql": "SELECT 1"}],
        [{"question": "pergunta", "sql": 1}],
        [{"question": "   ", "sql": "SELECT 1"}],
        [{"question": "pergunta", "sql": "   "}],
    ],
)
def test_malformed_example_payload_is_rejected(tmp_path, payload):
    path = _write_examples(tmp_path, payload)

    with pytest.raises(ValueError):
        rawmodel_module.RawModel._load_examples(path, 42)


def test_invalid_or_blank_json_is_not_silently_ignored(tmp_path):
    path = tmp_path / "examples.json"
    path.write_text("", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        rawmodel_module.RawModel._load_examples(str(path), 42)

    path.write_text("[]", encoding="utf-8")
    assert rawmodel_module.RawModel._load_examples(str(path), 42) == []


def test_missing_file_and_invalid_seed_are_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        rawmodel_module.RawModel._load_examples(str(tmp_path / "missing.json"), 42)

    path = _write_examples(tmp_path, _examples(1))
    with pytest.raises(ValueError):
        rawmodel_module.RawModel._load_examples(path, True)


def test_batch_resolver_reuses_the_same_examples_sources_as_existing_libraries():
    expected = {
        "datasus": "datasets/datasus/consultas_exemplo_reduzido.json",
        "sih_database": "datasets/sih_database/exemplos.json",
    }

    for database, path in expected.items():
        assert get_examples_path(database, "rawModel_exemplos") == path
        assert get_examples_path(database, "vannaAi_exemplos") == path
        assert get_examples_path(database, "XiYanSQL_exemplos") == path
        assert get_examples_path(database, "rawModel") is None
