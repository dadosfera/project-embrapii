"""Índice CATMAT sobre uma amostra real congelada do Snowflake (fixtures/catmat_amostra.json, 29/09/2026)."""
import json
from pathlib import Path

import pytest

from backend import catmat_index as ci
from backend.database import Q

AMOSTRA = json.loads((Path(__file__).parent / "fixtures" / "catmat_amostra.json").read_text())


@pytest.fixture(scope="module")
def ix():
    return ci.Indice(AMOSTRA)


def test_variantes_da_dipirona_500_viram_um_item(ix):
    g = ix.grupo("BR0267203")
    assert [v.codigo for v in g.variantes] == [
        "BR0267203", "BR0267203U0042", "BRBBR0267203U0042", "BROBR0267203U0042", "BRSBR0267203U0042",
    ]
    assert g.nome == "DIPIRONA SÓDICA, DOSAGEM:500 MG"
    assert g.tem_compras and g.tem_estoque
    assert g.variantes[2].rotulo == "Apresentação U0042 · BNAFAR B"


def test_grupo_por_id_de_qualquer_variante(ix):
    ids = ix.grupo("BR0267203").ids
    assert all(ix.grupo(i).base == "BR0267203" for i in ids)
    assert ix.grupo("BRSBR0267203U0042").base == "BR0267203"


def test_busca_sem_acento_e_ordem_principio_ativo_primeiro(ix):
    com, sem = ix.buscar("ácido fólico"), ix.buscar("acido folico")
    assert [g.base for g in com] == [g.base for g in sem] and com
    assert com[0].nome_norm.startswith("acido folico")
    associacoes = [i for i, g in enumerate(com) if g.associacao]
    puros = [i for i, g in enumerate(com) if not g.associacao and g.nome_norm.startswith("acido folico")]
    assert max(puros) < min(associacoes)


def test_busca_dipirona_nao_comeca_por_associacao(ix):
    r = ix.buscar("dipirona")
    assert r[0].composicao == "dipirona sodica" and not r[0].associacao
    assert len({g.base for g in r}) == len(r)  # nenhum item repetido


def test_busca_por_codigo_de_variante_ou_digitos(ix):
    assert ix.buscar("BROBR0267203U0042")[0].base == "BR0267203"
    assert ix.buscar("0267203")[0].base == "BR0267203"


def test_tokens_em_qualquer_ordem(ix):
    assert ix.buscar("lamotrigina 100")[0].base == "BR0272809"


def test_lixo_fora_da_busca_por_padrao(ix):
    todos = [v.codigo for g in ix.grupos.values() for v in g.variantes]
    assert not any("INATIV" in c or "TESTE" in c or c.startswith("BR0000000") for c in todos)
    assert ix.inativos


def test_sufixo_numerico_agrupa_apresentacoes(ix):
    g = ix.grupo("BR0104469")
    assert len(g.variantes) > 1 and {v.apresentacao for v in g.variantes} >= {None, "-1"}


def test_codigo_fora_do_padrao_vira_item_proprio(ix):
    nutricao = [g for g in ix.grupos.values() if g.base.startswith("BRNT")]
    assert nutricao and all(len(g.variantes) >= 1 for g in nutricao)


def test_composicao():
    assert ci.composicao_de("DIPIRONA SÓDICA, DOSAGEM:500 MG") == "dipirona sodica"
    assert ci.composicao_de("ÁCIDO FÓLICO 2 MG COMPRIMIDO") == "acido folico"
    assert ci.composicao_de("DIPIRONA + CAFEÍNA 500 + 65 MG COMPRIMIDO") == "dipirona + cafeina"
    assert ci.composicao_de("DIPIRONA SÓDICA, APRESENTAÇÃO:ASSOCIADA À ESCOPOLAMINA") == "dipirona sodica (associacao)"


def test_com_ids_troca_filtro_nas_duas_versoes():
    q = Q(pg="SELECT 1 FROM produto WHERE catmat_id = %(catmat_id)s", sf="SELECT 1 FROM produto p WHERE p.catmat_id = %(catmat_id)s")
    out = ci.com_ids(q, [3, 1, 2])
    assert out.pg.endswith("catmat_id IN (3, 1, 2)") and out.sf.endswith("catmat_id IN (3, 1, 2)")
    assert ci.com_ids(q, [7]) is q


def test_estoque_desconhecido_no_postgres():
    linhas = [{"catmat_id": 1, "codigo_catmat": "BR0000001", "descricao_catmat": "X", "tem_compras": True, "tem_estoque": None}]
    g = ci.Indice(linhas).grupo(1)
    assert g.tem_estoque is None and g.to_dict()["variantes"][0]["tem_estoque"] is None
