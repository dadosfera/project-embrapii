"""Filtros novos de /api/compras: fornecedor_id e uf (ver backend/api/compras.py _montar_filtros)."""
from backend.api import compras
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

ROTAS_COM_FILTROS_COMUNS = [
    "/api/compras/por-ano",
    "/api/compras/kpis",
    "/api/compras/por-mes",
    "/api/compras/fornecedores",
    "/api/compras/fabricantes",
    "/api/compras/modalidades",
    "/api/compras/tipos",
    "/api/compras/recentes",
]


def _fake_fetch(monkeypatch, capturado):
    def fake_all(query, params, *a, **k):
        capturado["query"] = query
        capturado["params"] = params
        return []

    def fake_one(query, params=None, *a, **k):
        capturado["query"] = query
        capturado["params"] = params
        return {}

    monkeypatch.setattr(compras, "fetch_all", fake_all)
    monkeypatch.setattr(compras, "fetch_one", fake_one)


def test_todas_as_rotas_aceitam_fornecedor_id_e_uf(monkeypatch):
    for rota in ROTAS_COM_FILTROS_COMUNS:
        capturado = {}
        _fake_fetch(monkeypatch, capturado)
        r = client.get(
            rota,
            params={
                "data_inicio": "2020-01-01",
                "data_fim": "2025-12-31",
                "fornecedor_id": 7,
                "uf": "mg",
            },
        )
        assert r.status_code == 200, f"{rota}: {r.text}"
        assert capturado["params"]["fornecedor_id"] == 7, rota
        assert capturado["params"]["uf"] == "MG", rota
        pg_sql = capturado["query"].for_engine("postgres")
        sf_sql = capturado["query"].for_engine("snowflake")
        assert "c.fornecedor_id = %(fornecedor_id)s" in pg_sql, rota
        assert "c.fornecedor_id = %(fornecedor_id)s" in sf_sql, rota
        assert "mun.sigla_uf = %(uf)s" in pg_sql, rota
        assert "mun.sigla_uf = %(uf)s" in sf_sql, rota


def test_uf_invalida_400():
    r = client.get(
        "/api/compras/kpis",
        params={"data_inicio": "2020-01-01", "data_fim": "2025-12-31", "uf": "XX"},
    )
    assert r.status_code == 400


def test_sem_uf_nem_fornecedor_nao_aparecem_nos_parametros(monkeypatch):
    capturado = {}
    _fake_fetch(monkeypatch, capturado)
    r = client.get(
        "/api/compras/kpis",
        params={"data_inicio": "2020-01-01", "data_fim": "2025-12-31"},
    )
    assert r.status_code == 200
    assert "fornecedor_id" not in capturado["params"]
    assert "uf" not in capturado["params"]
