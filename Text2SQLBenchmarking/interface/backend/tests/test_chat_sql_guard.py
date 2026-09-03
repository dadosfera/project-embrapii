import pytest
from interface.backend.chat.sql_guard import UnsafeSqlError, approve_read_only

@pytest.mark.parametrize("sql", ["SELECT 1", "SELECT ';' AS delimitador", "SELECT 1 /* comentário ; */", "SELECT 1;", "SELECT * FROM a JOIN b ON a.id=b.id", "WITH x AS (SELECT 1) SELECT * FROM x", "SELECT 1 UNION SELECT 2", "SELECT 'analyze' AS palavra", "SELECT 'copy' AS palavra", "SELECT 'into' AS palavra", "SELECT 'for update' AS texto"])
def test_guard_accepts_safe_corpus(sql): assert approve_read_only(sql)

@pytest.mark.parametrize("sql", ["", "SELECT FROM", "SELECT 'unterminated", "SELECT 1; SELECT 2", "INSERT INTO a VALUES (1)", "WITH x AS (DELETE FROM a RETURNING *) SELECT * FROM x", "SELECT * INTO a FROM b", "SELECT * FROM a FOR UPDATE", "EXPLAIN SELECT 1", "COPY a TO STDOUT", "SELECT pg_catalog.pg_sleep(1)", "SELECT pg_catalog.pg_terminate_backend(1)", "SELECT pg_catalog.set_config('x','y',false)", "SELECT public.dblink('x')", "SELECT pg_advisory_unlock(1)", "SELECT nextval('x')", "SELECT lo_import('x')", "SELECT pg_reload_conf()", "SELECT pg_ls_dir('.')"])
def test_guard_rejects_dangerous_corpus(sql):
    with pytest.raises(UnsafeSqlError): approve_read_only(sql)


@pytest.mark.parametrize("sql", [
    "SELECT * FROM (SELECT * FROM tabela FOR UPDATE) x",
    "WITH x AS (SELECT * FROM tabela FOR SHARE) SELECT * FROM x",
    "SELECT * FROM (SELECT * INTO destino FROM tabela) x",
    "SELECT lowrite(1, 'x')",
    "SELECT pg_catalog.lowrite(1, 'x')",
])
def test_guard_rejects_nested_locks_into_and_lowrite(sql):
    with pytest.raises(UnsafeSqlError): approve_read_only(sql)


def test_guard_still_accepts_dangerous_words_in_values_comments_and_aliases():
    assert approve_read_only("SELECT 'lowrite for update into' AS lowrite /* FOR SHARE */")
