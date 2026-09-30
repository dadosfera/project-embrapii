import pytest

from backend import database
from backend.database import Q


def test_q_escolhe_texto_por_engine():
    q = Q(pg="SELECT 1", sf="SELECT 2")
    assert q.for_engine("postgres") == "SELECT 1"
    assert q.for_engine("snowflake") == "SELECT 2"


def test_q_sem_sf_falha_no_snowflake():
    with pytest.raises(NotImplementedError):
        Q(pg="SELECT 1").for_engine("snowflake")


def test_engine_default_e_invalido(monkeypatch):
    monkeypatch.delenv("DB_ENGINE", raising=False)
    assert database.get_engine() == "postgres"
    monkeypatch.setenv("DB_ENGINE", "oracle")
    with pytest.raises(RuntimeError):
        database.get_engine()


@pytest.mark.parametrize("sql", ["DELETE FROM x", "  update x set a=1", "-- c\nDROP TABLE x"])
def test_guarda_select_only(sql):
    with pytest.raises(ValueError):
        database._assert_read_only(sql)


@pytest.mark.parametrize("sql", ["SELECT 1", "\n  -- comentario\n  WITH a AS (SELECT 1) SELECT * FROM a"])
def test_guarda_aceita_leitura(sql):
    database._assert_read_only(sql)


def test_fetch_all_normaliza_chaves(monkeypatch):
    monkeypatch.setenv("DB_ENGINE", "snowflake")
    monkeypatch.setattr(database, "_run", lambda engine, sql, params: [{"UF": "MG", "VALOR_TOTAL": 1}])
    assert database.fetch_all(Q(pg="SELECT 1", sf="SELECT 1")) == [{"uf": "MG", "valor_total": 1}]


def test_fetch_one_vazio(monkeypatch):
    monkeypatch.setattr(database, "_run", lambda engine, sql, params: [])
    assert database.fetch_one("SELECT 1") is None


def test_cache_bypass_com_cache_false(monkeypatch):
    monkeypatch.setattr(database.query_cache, "ttl", 3600)
    calls = []

    def fake_run(engine, sql, params):
        calls.append(1)
        return [{"result": len(calls)}]

    monkeypatch.setattr(database, "_run", fake_run)
    assert database.fetch_one("SELECT 1", cache=False) == {"result": 1}
    assert database.fetch_one("SELECT 1", cache=False) == {"result": 2}
    assert len(calls) == 2


def test_cache_key_usa_repr_para_diferenciar_tipos(monkeypatch):
    """1 (int) e "1" (str) não podem colidir na chave do cache."""
    monkeypatch.setattr(database.query_cache, "ttl", 3600)
    calls = []

    def fake_run(engine, sql, params):
        calls.append(params)
        return [{"n": params["v"]}]

    monkeypatch.setattr(database, "_run", fake_run)
    assert database.fetch_one("SELECT 1", {"v": 1}) == {"n": 1}
    assert database.fetch_one("SELECT 1", {"v": "1"}) == {"n": "1"}
    assert len(calls) == 2


def test_get_connection_read_only_e_utc(monkeypatch):
    import psycopg

    for var in ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]:
        monkeypatch.setenv(var, "x")
    captured = {}
    monkeypatch.setattr(psycopg, "connect", lambda **kw: captured.update(kw) or "conn")
    assert database.get_connection() == "conn"
    assert "-c default_transaction_read_only=on" in captured["options"]
    assert "-c TimeZone=UTC" in captured["options"]
