import pytest

from interface.backend.chat.sql_guard import UnsafeSqlError, approve_read_only
from interface.backend.chat.sql_normalizer import SqlNormalizationError, normalize_sql_output


OBSERVED_QWEN3 = """with PROC_REA and NOME_PROC. The user wants to know how many different
procedures are cadastrados...

Therefore, the SQL query should select...

SELECT COUNT(DISTINCT PROC_REA) FROM procedimentos;

...
</think>

SELECT COUNT(DISTINCT PROC_REA) FROM procedimentos;"""


def test_observed_qwen3_thinking_output_keeps_only_sql_after_last_think_close():
    assert normalize_sql_output(OBSERVED_QWEN3) == "SELECT COUNT(DISTINCT PROC_REA) FROM procedimentos;"


@pytest.mark.parametrize(("raw", "expected"), [
    ("<think>raciocínio</think>SELECT 1", "SELECT 1"),
    ("texto sem abertura </think> Query: SELECT 1", "SELECT 1"),
    ("```sql\nSELECT 1\n```", "SELECT 1"),
    ("```\nSELECT 1\n```", "SELECT 1"),
    ("A consulta é:\nSELECT 1;", "SELECT 1;"),
    ("SELECT 1;\n\nExplicação posterior.", "SELECT 1;"),
    ("SELECT ';' AS delimitador;\n\nExplicação posterior.", "SELECT ';' AS delimitador;"),
    ("WITH etapa AS (SELECT 1 AS id) SELECT id FROM etapa", "WITH etapa AS (SELECT 1 AS id) SELECT id FROM etapa"),
    ("SELECT COUNT(*) FROM procedimentos", "SELECT COUNT(*) FROM procedimentos"),
])
def test_normalizer_extracts_one_parseable_statement(raw, expected):
    assert normalize_sql_output(raw) == expected


@pytest.mark.parametrize("raw", ["sem SQL", "SELECT 1; SELECT 2"])
def test_normalizer_rejects_missing_or_multiple_statements(raw):
    with pytest.raises(SqlNormalizationError):
        normalize_sql_output(raw)


def test_normalized_dangerous_sql_is_left_for_the_read_only_guard():
    sql = normalize_sql_output("Resposta: DELETE FROM procedimentos")
    with pytest.raises(UnsafeSqlError):
        approve_read_only(sql)
