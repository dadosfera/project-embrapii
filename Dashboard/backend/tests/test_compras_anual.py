from datetime import date

from fastapi.testclient import TestClient

from backend.api import compras
from backend.main import app

client = TestClient(app)


def test_intervalo_deriva_anos_das_datas(monkeypatch):
    monkeypatch.setattr(
        compras,
        "fetch_one",
        lambda *a, **k: {"data_minima": date(2020, 1, 1), "data_maxima": date(2025, 1, 1)},
    )
    r = client.get("/api/compras/intervalo")
    assert r.status_code == 200
    assert r.json() == {
        "data_minima": "2020-01-01",
        "data_maxima": "2025-01-01",
        "ano_minimo": 2020,
        "ano_maximo": 2025,
    }


def test_intervalo_vazio(monkeypatch):
    # MIN/MAX é uma agregação sem GROUP BY: mesmo sem linhas na tabela, o banco
    # devolve uma linha só, com data_minima/data_maxima em NULL.
    monkeypatch.setattr(
        compras,
        "fetch_one",
        lambda *a, **k: {"data_minima": None, "data_maxima": None},
    )
    r = client.get("/api/compras/intervalo")
    assert r.status_code == 200
    assert r.json() == {
        "data_minima": None,
        "data_maxima": None,
        "ano_minimo": None,
        "ano_maximo": None,
    }


def test_intervalo_sem_linha_nenhuma(monkeypatch):
    """Defensivo: caso fetch_one alguma vez devolva None (nenhuma linha)."""
    monkeypatch.setattr(compras, "fetch_one", lambda *a, **k: None)
    r = client.get("/api/compras/intervalo")
    assert r.status_code == 200
    assert r.json() == {
        "data_minima": None,
        "data_maxima": None,
        "ano_minimo": None,
        "ano_maximo": None,
    }


def test_por_ano_repassa_filtros(monkeypatch):
    capturado = {}

    def fake(query, params, *a, **k):
        capturado["query"] = query
        capturado["params"] = params
        return []

    monkeypatch.setattr(compras, "fetch_all", fake)
    r = client.get(
        "/api/compras/por-ano",
        params={
            "data_inicio": "2020-01-01",
            "data_fim": "2025-12-31",
            "catmat_id": 85,
            "tipo_compra": "ADMINISTRATIVA",
        },
    )
    assert r.status_code == 200
    assert capturado["params"]["data_fim_exclusiva"] == date(2026, 1, 1)
    assert "catmat_id" in capturado["params"]
    sf_sql = capturado["query"].for_engine("snowflake")
    assert "YEAR(" in sf_sql
    assert "ROW_NUMBER()" in sf_sql


def test_por_ano_data_invertida_400():
    r = client.get(
        "/api/compras/por-ano",
        params={"data_inicio": "2025-12-31", "data_fim": "2020-01-01"},
    )
    assert r.status_code == 400


def test_por_ano_tipo_invalido_400():
    r = client.get(
        "/api/compras/por-ano",
        params={
            "data_inicio": "2020-01-01",
            "data_fim": "2025-12-31",
            "tipo_compra": "INVALIDA",
        },
    )
    assert r.status_code == 400
