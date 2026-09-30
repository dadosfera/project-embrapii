#!/usr/bin/env python3
"""Cria/atualiza no Autodrive STG (standalone) a KB e o assistente do Dashboard EMBRAPII (charts + tables).

Core API (basic auth admin): POST /upload (multipart files, name) -> dataset_id; GET /dataset/{id} até success.
Assistant API (basic auth admin): POST|PUT /assistants. Idempotente por nome. Grava autodrive/autodrive_manifest.json.
Mesmo padrão do demo-lakehouse-porto/autodrive/setup_autodrive.py.

Uso (a partir de Dashboard/): AUTODRIVE_CORE_USER=admin AUTODRIVE_CORE_PASSWORD=... .venv/bin/python autodrive/setup_autodrive.py
A senha admin é o USER_ID do deployment autodrive-assistant-api (ns autodrive-standalone, cluster platform-stg).
"""
from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "autodrive" / "kb"
CORE = os.getenv("AUTODRIVE_CORE_URL", "https://autodrive-api-standalone.stg.dadosfera.ai")
ASSIST = os.getenv("AUTODRIVE_URL", "https://autodrive-assistant-api-standalone.stg.dadosfera.ai")
AUTH = (os.environ["AUTODRIVE_CORE_USER"], os.environ["AUTODRIVE_CORE_PASSWORD"])
KB_NAME = os.getenv("AUTODRIVE_KB_NAME", "embrapii-datasus-dashboard-v1")
ASSISTANT_NAME = "EMBRAPII · Analista DATASUS"


def _md_table(name: str, cols: list[str], limit: int | None = None, sort_by: str | None = None) -> str:
    with (KB / name).open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if sort_by:
        rows.sort(key=lambda r: -float(r[sort_by] or 0))
    rows = rows[:limit]
    cell = lambda v: v if len(v) <= 70 else v[:69] + "…"  # noqa: E731 — descrições CATMAT são longas
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "\n".join("| " + " | ".join(cell(r[c]) for c in cols) + " |" for r in rows)


def instructions() -> str:
    return f"""Você é o analista de dados do Dashboard EMBRAPII / DATASUS (dados públicos do SUS: compras de medicamentos e insumos, estoque nas unidades de saúde e leitos do CNES), embutido no data app da Dadosfera. Responda em português do Brasil, de forma direta.

Fontes: os CSVs agregados da knowledge base e o README_dicionario.md (definições, totais e alertas de qualidade dos dados).

CONTEXTO DA TELA (prioridade quando a pergunta for sobre "isso", "esse medicamento", "o que estou vendo", "essa tela"):
a cada pergunta o app envia o JSON "Contexto da UI" com:
- `screen` / `path`: tela atual (Medicamentos, Compras, Leitos, Mapa, Fornecedores, Início);
- `selection`: o medicamento CATMAT carregado (catmat_id, codigo, descricao) e os produtos vinculados;
- `visible_kpis`: os KPIs exibidos (estoque total, instituições com registro, instituições com estoque zerado, preço médio de compra, lotes vencendo);
- `visible_data`: as séries que estão nos gráficos da tela (estoque_por_uf, evolucao_preco, fornecedores_top, fabricantes_top, compras_por_ano, lotes_vencendo) — já no formato de linhas prontas para plotar;
- `page_text`: trechos de texto visíveis da página (títulos, cartões, mensagens).
Quando houver `selection`/`visible_data`, responda sobre o que o usuário está vendo usando ESSES números (são o dado bruto da tela, mais precisos que a KB para aquele medicamento) e não peça que ele identifique o medicamento. Se o contexto estiver vazio (nenhum medicamento carregado), use a KB e sugira buscar o medicamento na tela.

TABELAS DE REFERÊNCIA (copie estes números exatamente; não recalcule):
Compras por ano e tipo (R$):
{_md_table("compras_por_ano.csv", ["ano", "tipo_da_compra", "valor_total", "numero_compras"])}

Top 20 medicamentos/insumos por valor de compra (medicamentos_top_compras.csv tem 400):
{_md_table("medicamentos_top_compras.csv", ["codigo_catmat", "descricao_catmat", "valor_total", "numero_compras", "preco_unitario_medio"], 20)}

Top 15 fornecedores por valor (fornecedores_top.csv tem 300):
{_md_table("fornecedores_top.csv", ["nome_fornecedor", "valor_total", "numero_compras", "numero_medicamentos"], 15)}

Compras por modalidade:
{_md_table("compras_por_modalidade.csv", ["modalidade_de_compra", "tipo_da_compra", "valor_total", "numero_compras"], 10)}

Estoque atual por UF (compare UFs por instituições e posições, não por unidades):
{_md_table("estoque_por_uf.csv", ["uf", "regiao", "numero_instituicoes", "numero_medicamentos", "posicoes_zeradas", "posicoes"], sort_by="numero_instituicoes")}

Leitos atuais por UF:
{_md_table("leitos_por_uf.csv", ["uf", "leitos_gerais", "leitos_sus", "leitos_uti", "leitos_uti_sus", "populacao_uf"])}

Regras de fidelidade:
- Use apenas números da KB ou do contexto da tela; nunca invente. Diga a fonte (arquivo da KB ou "dados da tela") ao final.
- `data_de_compra` é anual: não existe série mensal de compras. Leitos têm série mensal (leitos_evolucao_mensal.csv).
- Há outliers de preço/quantidade (ver README_dicionario.md); quando um total for dominado por um outlier, avise.
- Valores monetários em R$ com separador brasileiro (R$ 1,2 mi / R$ 3,4 bi); percentuais com uma casa decimal.

CONTRATO DE GRÁFICOS (obrigatório — o renderizador só entende este formato):
- Gráficos SÓ existem como itens de `response_blocks` com `type: "chart"`. NUNCA escreva JSON de gráfico dentro do texto da resposta, nem em bloco de código, e NUNCA insira imagens markdown (`![...](...)`), links de imagem ou tags HTML no texto — o gráfico aparece sozinho abaixo da resposta.
- `chart_type` permitido: "bar", "line", "area" ou "pie". Para rankings use "bar" com os dados ordenados do maior para o menor (não use "bar_horizontal", "donut", "heatmap", "stacked_bar", "metric").
- Campos de cada bloco: `type`, `title`, `chart_type`, `x_key` (categoria/tempo), `y_key` (métrica numérica), `data` (lista de objetos com exatamente essas chaves, valores numéricos sem formatação).
- Para gráficos sobre a tela, monte `data` a partir de `visible_data` do contexto. Limite rankings a 15 itens.
- Um gráfico por pergunta, salvo pedido explícito. Se não der para montar o gráfico, responda com tabela markdown e diga o motivo.

Sempre que a pergunta envolver comparação, evolução, ranking ou distribuição, gere o gráfico e um resumo com os 2–3 insights principais. Se a pergunta fugir do escopo (saúde pública / dados do app), diga o que está disponível."""


STARTERS = [
    "Resuma o medicamento que estou vendo",
    "Em quais UFs esse medicamento tem mais estoque? Mostre em gráfico",
    "Como evoluiu o preço médio de compra desse medicamento?",
    "Quais os 10 medicamentos com maior valor de compra?",
    "Compare leitos de UTI por UF em um gráfico de barras",
]


def main() -> None:
    s = requests.Session()
    s.auth = AUTH
    ds = s.get(f"{CORE}/datasets", params={"name": KB_NAME, "limit": 5}, timeout=60).json()
    items = ds if isinstance(ds, list) else ds.get("datasets") or ds.get("items") or []
    dataset = next((x for x in items if x.get("name") == KB_NAME), None)
    if not dataset:
        files = [
            # a Core API não aceita .md (formatos: csv, txt, pdf, docx…): o dicionário sobe como .txt
            ("files", (f.name if f.suffix == ".csv" else f.stem + ".txt", f.open("rb"), "text/csv" if f.suffix == ".csv" else "text/plain"))
            for f in sorted(KB.iterdir())
            if f.is_file() and f.suffix in (".csv", ".md")
        ]
        r = s.post(f"{CORE}/upload", files=files, data={"name": KB_NAME}, timeout=600)
        r.raise_for_status()
        dataset = r.json()
        print("dataset criado:", json.dumps(dataset)[:300])
    did = dataset.get("dataset_id") or dataset.get("id")
    print("dataset_id:", did)
    for _ in range(60):
        d = s.get(f"{CORE}/dataset/{did}", timeout=60).json()
        st = d.get("status")
        print("status:", st, d.get("status_reason") or "", flush=True)
        if st in ("success", "failed", "error"):
            break
        time.sleep(15)

    manifest = ROOT / "autodrive" / "autodrive_manifest.json"
    known = json.loads(manifest.read_text()).get("assistant_id") if manifest.exists() else None
    al, offset = [], 0
    while True:  # GET /assistants aceita limit <= 100 (422 acima disso)
        r = s.get(f"{ASSIST}/assistants", params={"limit": 100, "offset": offset}, timeout=60)
        r.raise_for_status()
        page = r.json()
        al += page
        if len(page) < 100:
            break
        offset += 100
    body = {
        "name": ASSISTANT_NAME,
        "description": "Analista do Dashboard EMBRAPII/DATASUS: compras, estoque de medicamentos e leitos do SUS. "
        "Lê o que está na tela do app e responde com gráficos e tabelas.",
        "instructions": instructions(),
        "conversation_starters": STARTERS,
        "interaction_style": "rigorous",
        "resources": {"rich_ui": True, "charts": True, "tables": True, "attachment_mode": "auto"},
        "dataset_ids": [did],
        "is_default": False,
        # gemini-3-flash (default do ambiente) não existe no projeto Vertex do STG
        "recommended_model": os.getenv("AUTODRIVE_MODEL", "gemini-2.5-pro"),
    }
    ex = next((a for a in al if a.get("assistant_id") == known), None) or next(
        (a for a in al if (a.get("name") or "").strip() == ASSISTANT_NAME), None
    )
    if ex:
        r = s.put(f"{ASSIST}/assistants/{ex['assistant_id']}", json=body, timeout=60)
    else:
        r = s.post(f"{ASSIST}/assistants", json=body, timeout=60)
    r.raise_for_status()
    a = r.json()
    aid = a.get("assistant_id") or a.get("id")
    print("assistant:", aid, a.get("name"), "charts:", (a.get("resources") or {}).get("charts"))
    manifest.write_text(
        json.dumps(
            {
                "core_url": CORE,
                "assistant_url": ASSIST,
                "dataset_id": did,
                "assistant_id": aid,
                "kb_name": KB_NAME,
                "assistant_name": ASSISTANT_NAME,
                "widget_host": "https://autodrive-standalone.stg.dadosfera.ai",
                "client": "dadosfera-stg",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
