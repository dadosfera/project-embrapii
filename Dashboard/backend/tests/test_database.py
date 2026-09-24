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
