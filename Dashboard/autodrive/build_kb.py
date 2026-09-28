#!/usr/bin/env python3
"""Gera a knowledge base do assistente Autodrive a partir do Snowflake (EMBRAPII_DATASUS).

Só agregados: cada CSV fica com poucas centenas/milhares de linhas, para caber no contexto do LLM e na
detecção de schema dos gráficos do Autodrive. O dado bruto de uma tela (medicamento selecionado) vai pelo
`ui_context` do widget, não pela KB.

Uso (a partir de Dashboard/): set -a; source .env; set +a;
  DB_ENGINE=snowflake SNOWFLAKE_DATABASE=DADOSFERA_PRD_DADOSFERADEMO .venv/bin/python autodrive/build_kb.py
Saída: autodrive/kb/*.csv + autodrive/kb/_totais.json (lido pelo setup_autodrive.py).
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.database import Q, fetch_all  # noqa: E402

KB = ROOT / "autodrive" / "kb"

# Última posição de estoque por instituição × CATMAT (mesma regra do /resumo da tela de Medicamentos).
_ESTOQUE_ATUAL = """
    estoque_atual AS (
        SELECT iep.instituicao_id, p.catmat_id, iep.quantidade_do_item_em_estoque AS qtd, iep.data_de_validade
        FROM instituicao_estoca_produto iep
        JOIN produto p ON p.produto_id = iep.produto_id
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY iep.instituicao_id, p.catmat_id
            ORDER BY iep.data_de_posicao_no_estoque DESC NULLS LAST, iep.instituicao_estoca_produto_id DESC
        ) = 1
    )"""

# Último snapshot de leitos por instituição.
_LEITOS_ATUAL = """
    leitos_atual AS (
        SELECT l.*
        FROM leitos l
        QUALIFY ROW_NUMBER() OVER (PARTITION BY l.instituicao_id ORDER BY l.data_de_competencia DESC, l.leitos_id DESC) = 1
    )"""

QUERIES: dict[str, str] = {
    # Compras (mantenedora_compra_produto)
    # data_de_compra na base é anual (sempre 1º de janeiro), por isso o grão é ano.
    "compras_por_ano.csv": """
        SELECT YEAR(c.data_de_compra) AS ano,
               COALESCE(c.tipo_da_compra, 'NÃO INFORMADO') AS tipo_da_compra,
               ROUND(SUM(c.preco_total), 2) AS valor_total, COUNT(*) AS numero_compras,
               SUM(c.quantidade_de_itens) AS quantidade_itens
        FROM mantenedora_compra_produto c
        WHERE c.data_de_compra IS NOT NULL
        GROUP BY 1, 2 ORDER BY 1, 2""",
    "compras_por_uf_ano.csv": """
        SELECT COALESCE(m.sigla_uf, 'N/I') AS uf, YEAR(c.data_de_compra) AS ano,
               ROUND(SUM(c.preco_total), 2) AS valor_total, COUNT(*) AS numero_compras,
               COUNT(DISTINCT c.mantenedora_id) AS numero_mantenedoras
        FROM mantenedora_compra_produto c
        LEFT JOIN mantenedora mt ON mt.mantenedora_id = c.mantenedora_id
        LEFT JOIN municipio m ON m.codigo_do_municipio = mt.municipio_id
        WHERE c.data_de_compra IS NOT NULL
        GROUP BY 1, 2 ORDER BY 1, 2""",
    "compras_por_modalidade.csv": """
        SELECT COALESCE(NULLIF(TRIM(c.modalidade_de_compra), ''), 'Não informado') AS modalidade_de_compra,
               COALESCE(c.tipo_da_compra, 'NÃO INFORMADO') AS tipo_da_compra,
               ROUND(SUM(c.preco_total), 2) AS valor_total, COUNT(*) AS numero_compras
        FROM mantenedora_compra_produto c
        GROUP BY 1, 2 ORDER BY valor_total DESC""",
    "medicamentos_top_compras.csv": """
        SELECT ct.catmat_id, ct.codigo_catmat, ct.descricao_catmat,
               ROUND(SUM(c.preco_total), 2) AS valor_total, COUNT(*) AS numero_compras,
               SUM(c.quantidade_de_itens) AS quantidade_itens,
               ROUND(AVG(c.preco_unitario), 4) AS preco_unitario_medio,
               ROUND(MIN(c.preco_unitario), 4) AS preco_unitario_min,
               ROUND(MAX(c.preco_unitario), 4) AS preco_unitario_max,
               COUNT(DISTINCT c.fornecedor_id) AS numero_fornecedores,
               COUNT(DISTINCT c.mantenedora_id) AS numero_mantenedoras,
               MIN(c.data_de_compra) AS primeira_compra, MAX(c.data_de_compra) AS ultima_compra
        FROM mantenedora_compra_produto c
        JOIN produto p ON p.produto_id = c.produto_id
        JOIN catmat ct ON ct.catmat_id = p.catmat_id
        GROUP BY 1, 2, 3 ORDER BY valor_total DESC NULLS LAST LIMIT 400""",
    "medicamentos_preco_por_ano.csv": """
        WITH top AS (
            SELECT p.catmat_id FROM mantenedora_compra_produto c JOIN produto p ON p.produto_id = c.produto_id
            GROUP BY 1 ORDER BY SUM(c.preco_total) DESC NULLS LAST LIMIT 100
        )
        SELECT ct.catmat_id, ct.descricao_catmat, YEAR(c.data_de_compra) AS ano,
               ROUND(AVG(c.preco_unitario), 4) AS preco_unitario_medio,
               ROUND(SUM(c.preco_total), 2) AS valor_total, COUNT(*) AS numero_compras
        FROM mantenedora_compra_produto c
        JOIN produto p ON p.produto_id = c.produto_id
        JOIN top t ON t.catmat_id = p.catmat_id
        JOIN catmat ct ON ct.catmat_id = p.catmat_id
        WHERE c.data_de_compra IS NOT NULL AND c.preco_unitario IS NOT NULL
        GROUP BY 1, 2, 3 ORDER BY 1, 3""",
    "fornecedores_top.csv": """
        SELECT COALESCE(NULLIF(TRIM(f.nome_fornecedor), ''), 'Não informado') AS nome_fornecedor, f.cnpj_fornecedor,
               ROUND(SUM(c.preco_total), 2) AS valor_total, COUNT(*) AS numero_compras,
               COUNT(DISTINCT p.catmat_id) AS numero_medicamentos, COUNT(DISTINCT c.mantenedora_id) AS numero_mantenedoras
        FROM mantenedora_compra_produto c
        LEFT JOIN fornecedor f ON f.fornecedor_id = c.fornecedor_id
        LEFT JOIN produto p ON p.produto_id = c.produto_id
        GROUP BY 1, 2 ORDER BY valor_total DESC NULLS LAST LIMIT 300""",
    "fabricantes_top.csv": """
        SELECT COALESCE(NULLIF(TRIM(fb.nome_fabricante), ''), 'Não informado') AS nome_fabricante, fb.cnpj_fabricante,
               ROUND(SUM(c.preco_total), 2) AS valor_total, COUNT(*) AS numero_compras,
               COUNT(DISTINCT p.catmat_id) AS numero_medicamentos
        FROM mantenedora_compra_produto c
        LEFT JOIN fabricante fb ON fb.fabricante_id = c.fabricante_id
        LEFT JOIN produto p ON p.produto_id = c.produto_id
        GROUP BY 1, 2 ORDER BY valor_total DESC NULLS LAST LIMIT 300""",
    # Estoque (instituicao_estoca_produto — recorte com a posição mais recente por instituição × produto)
    "estoque_por_uf.csv": f"""
        WITH {_ESTOQUE_ATUAL}
        SELECT COALESCE(v.sigla_unidade_federativa, 'N/I') AS uf, COALESCE(v.regiao_do_brasil, 'N/I') AS regiao,
               SUM(e.qtd) AS estoque_total, COUNT(DISTINCT e.instituicao_id) AS numero_instituicoes,
               COUNT(DISTINCT e.catmat_id) AS numero_medicamentos,
               COUNT_IF(e.qtd = 0) AS posicoes_zeradas, COUNT(*) AS posicoes
        FROM estoque_atual e
        JOIN instituicao i ON i.instituicao_id = e.instituicao_id
        LEFT JOIN v_endereco_completo v ON v.endereco_id = i.endereco_id
        GROUP BY 1, 2 ORDER BY estoque_total DESC""",
    "medicamentos_top_estoque.csv": f"""
        WITH {_ESTOQUE_ATUAL}
        SELECT ct.catmat_id, ct.codigo_catmat, ct.descricao_catmat,
               SUM(e.qtd) AS estoque_total, COUNT(DISTINCT e.instituicao_id) AS instituicoes_com_registro,
               COUNT_IF(e.qtd = 0) AS instituicoes_estoque_zerado,
               COUNT_IF(e.data_de_validade >= CURRENT_DATE() AND e.data_de_validade < DATEADD(day, 90, CURRENT_DATE()) AND e.qtd > 0)
                   AS posicoes_vencendo_90d
        FROM estoque_atual e
        JOIN catmat ct ON ct.catmat_id = e.catmat_id
        GROUP BY 1, 2, 3 ORDER BY instituicoes_com_registro DESC LIMIT 400""",
    # Leitos (CNES) — último snapshot por instituição
    "leitos_por_uf.csv": f"""
        WITH {_LEITOS_ATUAL}
        SELECT COALESCE(mun.sigla_uf, 'N/I') AS uf,
               SUM(l.quantidade_leitos_gerais) AS leitos_gerais, SUM(l.quantidade_leitos_sus) AS leitos_sus,
               SUM(l.quantidade_leitos_uti) AS leitos_uti, SUM(l.quantidade_leitos_uti_sus) AS leitos_uti_sus,
               SUM(l.quantidade_leitos_uti_adulto) AS uti_adulto, SUM(l.quantidade_leitos_uti_pediatrico) AS uti_pediatrico,
               SUM(l.quantidade_leitos_uti_neonatal) AS uti_neonatal, SUM(l.quantidade_leitos_uti_coronariana) AS uti_coronariana,
               SUM(l.quantidade_leitos_uti_queimado) AS uti_queimado,
               COUNT(DISTINCT l.instituicao_id) AS numero_instituicoes,
               MAX(mun_pop.populacao) AS populacao_uf
        FROM leitos_atual l
        JOIN instituicao i ON i.instituicao_id = l.instituicao_id
        LEFT JOIN endereco e ON e.endereco_id = i.endereco_id
        LEFT JOIN municipio mun ON mun.codigo_do_municipio = e.municipio_id
        LEFT JOIN (SELECT sigla_uf, SUM(populacao) AS populacao FROM municipio GROUP BY 1) mun_pop ON mun_pop.sigla_uf = mun.sigla_uf
        GROUP BY 1 ORDER BY leitos_gerais DESC""",
    "leitos_evolucao_mensal.csv": """
        SELECT TO_CHAR(l.data_de_competencia, 'YYYY-MM') AS competencia,
               SUM(l.quantidade_leitos_gerais) AS leitos_gerais, SUM(l.quantidade_leitos_sus) AS leitos_sus,
               SUM(l.quantidade_leitos_uti) AS leitos_uti, SUM(l.quantidade_leitos_uti_sus) AS leitos_uti_sus,
               COUNT(DISTINCT l.instituicao_id) AS numero_instituicoes
        FROM leitos l
        GROUP BY 1 ORDER BY 1""",
}

TOTAIS = {
    "compras": """SELECT COUNT(*) AS n, ROUND(SUM(preco_total), 2) AS valor, MIN(data_de_compra) AS inicio,
                         MAX(data_de_compra) AS fim, COUNT(DISTINCT fornecedor_id) AS fornecedores,
                         COUNT(DISTINCT mantenedora_id) AS mantenedoras FROM mantenedora_compra_produto""",
    "catalogo": "SELECT (SELECT COUNT(*) FROM catmat) AS catmat, (SELECT COUNT(*) FROM produto) AS produtos, (SELECT COUNT(*) FROM instituicao) AS instituicoes",
    "estoque": """SELECT COUNT(*) AS posicoes, MIN(data_de_posicao_no_estoque) AS inicio, MAX(data_de_posicao_no_estoque) AS fim
                  FROM instituicao_estoca_produto""",
    "leitos": "SELECT MIN(data_de_competencia) AS inicio, MAX(data_de_competencia) AS fim FROM leitos",
}


def _plain(v):
    if isinstance(v, Decimal):
        return float(v) if v != v.to_integral_value() else int(v)
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()[:10]
    return v


def run(sql: str) -> list[dict]:
    return [{k.lower(): _plain(v) for k, v in r.items()} for r in fetch_all(Q(pg="SELECT 1", sf=sql), {}, cache=False)]


def main() -> None:
    KB.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    for name, sql in QUERIES.items():
        if only and name not in only:
            continue
        rows = run(sql)
        with (KB / name).open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["vazio"])
            w.writeheader()
            w.writerows(rows)
        print(f"{name}: {len(rows)} linhas", flush=True)
    totais = {k: run(sql)[0] for k, sql in TOTAIS.items()}
    (KB / "_totais.json").write_text(json.dumps(totais, ensure_ascii=False, indent=2))
    print(json.dumps(totais, ensure_ascii=False))


if __name__ == "__main__":
    main()
