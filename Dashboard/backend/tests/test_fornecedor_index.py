"""Índice de fornecedores sobre uma amostra pequena, sem banco (ver backend/fornecedor_index.py)."""
import pytest

from backend import fornecedor_index as fi

AMOSTRA = [
    {
        "fornecedor_id": 1,
        "nome_fornecedor": "DIMEVA DISTRIBUIDORA DE MEDICAMENTOS LTDA",
        "cnpj_fornecedor": "12345678000199",
        "valor_total": 500_000,
        "numero_compras": 42,
    },
    {
        "fornecedor_id": 2,
        "nome_fornecedor": "DISTRIBUIDORA HOSPITALAR DIMEVA DO BRASIL",
        "cnpj_fornecedor": "98765432000111",
        "valor_total": 1_000_000,
        "numero_compras": 10,
    },
    {
        "fornecedor_id": 3,
        "nome_fornecedor": "MEDICAL MERCANTIL LTDA",
        "cnpj_fornecedor": "11122233000144",
        "valor_total": 200_000,
        "numero_compras": 5,
    },
    {
        "fornecedor_id": 4,
        "nome_fornecedor": "ÚNICA COMÉRCIO DE PRODUTOS HOSPITALARES",
        "cnpj_fornecedor": "22233344000155",
        "valor_total": 50_000,
        "numero_compras": 2,
    },
    {
        "fornecedor_id": 5,
        "nome_fornecedor": "HOSPITALAR ABC LTDA",
        "cnpj_fornecedor": "33344455000166",
        "valor_total": 300_000,
        "numero_compras": 7,
    },
    {
        "fornecedor_id": 6,
        "nome_fornecedor": "HOSPITALAR XYZ LTDA",
        "cnpj_fornecedor": "44455566000177",
        "valor_total": 900_000,
        "numero_compras": 3,
    },
]


@pytest.fixture(scope="module")
def ix():
    return fi.Indice(AMOSTRA)


def test_cnpj_exato_vem_primeiro(ix):
    r = ix.buscar("12345678000199")
    assert r[0].fornecedor_id == 1


def test_cnpj_exato_com_mascara(ix):
    r = ix.buscar("12.345.678/0001-99")
    assert r[0].fornecedor_id == 1


def test_nome_comeca_com_o_termo_vem_antes_de_conter_no_meio(ix):
    r = ix.buscar("dimeva")
    # "DIMEVA DISTRIBUIDORA..." comeca com o termo; "DISTRIBUIDORA HOSPITALAR DIMEVA..." só
    # tem uma palavra que começa com o termo (faixa 2) — o primeiro vem antes.
    assert [f.fornecedor_id for f in r][:2] == [1, 2]


def test_busca_sem_acento(ix):
    r = ix.buscar("unica")
    assert any(f.fornecedor_id == 4 for f in r)


def test_tokens_em_qualquer_ordem(ix):
    r = ix.buscar("hospitalar distribuidora")
    assert any(f.fornecedor_id == 2 for f in r)


def test_cnpj_contem_pelo_menos_4_digitos(ix):
    r = ix.buscar("6543")
    assert any(f.fornecedor_id == 2 for f in r)


def test_cnpj_com_menos_de_4_digitos_nao_acha_por_substring(ix):
    r = ix.buscar("654")
    assert not any(f.fornecedor_id == 2 for f in r)


def test_nome_comeca_com_o_termo_vem_antes_de_conter_no_meio_2(ix):
    # "DISTRIBUIDORA HOSPITALAR..." começa com o termo (faixa 1); "DIMEVA DISTRIBUIDORA..."
    # só tem "distribuidora" como palavra no meio (faixa 2) — o que começa vem primeiro,
    # mesmo tendo valor_total menor.
    r = ix.buscar("distribuidora")
    ids = [f.fornecedor_id for f in r if f.fornecedor_id in (1, 2)]
    assert ids == [2, 1]


def test_empate_de_faixa_desempata_por_valor_total_desc(ix):
    # "hospitalar ltda" não é substring contígua em nenhum dos dois nomes (tem "abc"/"xyz"
    # no meio) — os dois caem na faixa "contém todos os tokens, em qualquer ordem" (faixa 3).
    # O de maior valor_total (fornecedor 6) deve vir antes do 5.
    r = ix.buscar("hospitalar ltda")
    ids = [f.fornecedor_id for f in r if f.fornecedor_id in (5, 6)]
    assert ids == [6, 5]


def test_limite_respeitado(ix):
    assert len(ix.buscar("ltda", limite=2)) == 2


def test_termo_vazio_nao_acha_nada(ix):
    assert ix.buscar("   ") == []


def test_buscar_modulo_devolve_dicts(monkeypatch, ix):
    monkeypatch.setattr(fi, "indice", lambda: ix)
    resultado = fi.buscar("dimeva", 5)
    assert resultado[0]["fornecedor_id"] == 1
    assert set(resultado[0]) == {"fornecedor_id", "nome", "cnpj", "valor_total", "numero_compras"}
