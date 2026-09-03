from __future__ import annotations

import sys
from unittest.mock import Mock

import src.rawmodel as rawmodel_module

# Os adapters devem continuar importando o legado apenas em load(). Mantemos a
# referência para os mocks, mas não deixamos o módulo parecer carregado à suíte.
sys.modules.pop("src.rawmodel", None)


def _raw_model_without_loading() -> rawmodel_module.RawModel:
    return object.__new__(rawmodel_module.RawModel)


def test_raw_model_sends_messages_directly_to_pipeline_without_thinking_argument():
    model = _raw_model_without_loading()
    messages = [{"role": "user", "content": "pergunta"}]
    model.pipe = Mock(return_value=[{"generated_text": "SELECT 1"}])

    assert model._infer_local(messages) == "SELECT 1"
    model.pipe.assert_called_once_with(messages, max_new_tokens=512, do_sample=False, return_full_text=False)


def test_raw_model_removes_thinking_after_generation_and_keeps_only_final_sql():
    model = _raw_model_without_loading()
    raw = "<think>exemplo SELECT interno FROM segredo</think>\n\nSELECT COUNT(DISTINCT PROC_REA) FROM procedimentos;"
    assert model._extract_sql(raw) == "SELECT COUNT(DISTINCT PROC_REA) FROM procedimentos;"


def test_raw_model_uses_sql_after_last_think_closing_and_keeps_pure_sql():
    model = _raw_model_without_loading()
    assert model._extract_sql("texto </think> SELECT 2") == "SELECT 2"
    assert model._extract_sql("SELECT 3") == "SELECT 3"


def test_raw_model_schema_inspect_remains_sqlalchemy_inspect(monkeypatch):
    model = _raw_model_without_loading()
    model.db_uri = "synthetic://database"
    model._schema_cache = {}
    model.engine = object()
    inspector = Mock()
    inspector.get_table_names.return_value = []
    sqlalchemy_inspect = rawmodel_module.inspect
    assert sqlalchemy_inspect.__module__.startswith("sqlalchemy")
    monkeypatch.setattr(rawmodel_module, "inspect", Mock(return_value=inspector))

    assert model._get_schema() == ""
    rawmodel_module.inspect.assert_called_once_with(model.engine)
