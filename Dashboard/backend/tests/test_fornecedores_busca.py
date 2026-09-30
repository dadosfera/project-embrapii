from fastapi.testclient import TestClient

from backend.api import fornecedores
from backend.main import app

client = TestClient(app)


def test_busca_autocomplete_chama_indice(monkeypatch):
    capturado = {}

    def fake(termo, limite):
        capturado["termo"] = termo
        capturado["limite"] = limite
        return [{"fornecedor_id": 1, "nome": "DIMEVA", "cnpj": "123", "valor_total": 10.0, "numero_compras": 2}]

    monkeypatch.setattr(fornecedores.fornecedor_index, "buscar", fake)
    r = client.get("/api/fornecedores/busca", params={"q": "dimeva", "limite": 5})
    assert r.status_code == 200
    assert capturado == {"termo": "dimeva", "limite": 5}
    assert r.json()[0]["fornecedor_id"] == 1


def test_busca_autocomplete_exige_q():
    r = client.get("/api/fornecedores/busca")
    assert r.status_code == 422


def test_busca_autocomplete_limite_padrao_20(monkeypatch):
    capturado = {}

    def fake(termo, limite):
        capturado["limite"] = limite
        return []

    monkeypatch.setattr(fornecedores.fornecedor_index, "buscar", fake)
    client.get("/api/fornecedores/busca", params={"q": "dimeva"})
    assert capturado["limite"] == 20


def test_ranking_com_fornecedor_id_repassa_filtro(monkeypatch):
    capturado = {}

    def fake(query, params, *a, **k):
        capturado["query"] = query
        capturado["params"] = params
        return []

    monkeypatch.setattr(fornecedores, "fetch_all", fake)
    r = client.get(
        "/api/fornecedores/ranking",
        params={"data_inicio": "2020-01-01", "data_fim": "2025-12-31", "fornecedor_id": 42},
    )
    assert r.status_code == 200
    assert capturado["params"]["fornecedor_id"] == 42
    pg_sql = capturado["query"].for_engine("postgres")
    sf_sql = capturado["query"].for_engine("snowflake")
    assert "c.fornecedor_id = %(fornecedor_id)s" in pg_sql
    assert "c.fornecedor_id = %(fornecedor_id)s" in sf_sql


def test_ranking_sem_fornecedor_id_nao_filtra(monkeypatch):
    capturado = {}

    def fake(query, params, *a, **k):
        capturado["params"] = params
        return []

    monkeypatch.setattr(fornecedores, "fetch_all", fake)
    client.get(
        "/api/fornecedores/ranking",
        params={"data_inicio": "2020-01-01", "data_fim": "2025-12-31"},
    )
    assert "fornecedor_id" not in capturado["params"]
