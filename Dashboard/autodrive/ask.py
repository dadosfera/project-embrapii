#!/usr/bin/env python3
"""Pergunta ao assistente Autodrive como o widget faria, com o ui_context da tela de Medicamentos.

O contexto é montado com as mesmas funções da API do app (backend.api.medicamentos), no mesmo formato que o
front publica em window.__embrapiiUiContext. Útil para validar instruções/gráficos sem abrir o browser.

Uso (a partir de Dashboard/): set -a; source .env; set +a; AUTODRIVE_AUTH_CLIENT_ID=... AUTODRIVE_AUTH_CLIENT_SECRET=... \
  DB_ENGINE=snowflake SNOWFLAKE_DATABASE=DADOSFERA_PRD_DADOSFERADEMO .venv/bin/python autodrive/ask.py "pergunta" [catmat_id]
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MANIFEST = json.loads((ROOT / "autodrive" / "autodrive_manifest.json").read_text())
URL = MANIFEST["assistant_url"]
ORIGIN = os.getenv("AUTODRIVE_PROXY_ORIGIN", "https://app-intelligence-dadosferademo.dadosfera.ai")


def ui_context(catmat_id: int | None) -> dict:
    if catmat_id is None:
        return {"app": "Dashboard EMBRAPII / DATASUS", "screen": "Medicamentos", "path": "/medicamentos",
                "description": "Nenhum medicamento carregado."}
    from backend.api import medicamentos as m
    from backend.database import Q, fetch_one

    cat = fetch_one(Q(pg="", sf="SELECT catmat_id, codigo_catmat, descricao_catmat FROM catmat WHERE catmat_id = %(c)s"), {"c": catmat_id})
    cat = {k.lower(): v for k, v in cat.items()}
    resumo = m.resumo_medicamento(catmat_id)
    lotes = m.lotes_vencendo(catmat_id, 90)
    num = lambda v: float(v) if v is not None else None  # noqa: E731
    return {
        "app": "Dashboard EMBRAPII / DATASUS",
        "screen": "Medicamentos",
        "path": "/medicamentos",
        "selection": {"catmat_id": catmat_id, "codigo_catmat": cat["codigo_catmat"], "descricao": cat["descricao_catmat"],
                      "produtos": len(m.listar_produtos_do_catmat(catmat_id))},
        "visible_kpis": {"estoque_total": num(resumo["estoque_total"]), "instituicoes_com_registro": resumo["instituicoes_com_registro"],
                         "instituicoes_estoque_zerado": resumo["instituicoes_estoque_zerado"],
                         "preco_medio_compra": num(resumo["preco_medio_compra"]), "lotes_vencendo_90d": lotes["quantidade_lotes"]},
        "visible_data": {
            "estoque_por_uf": [{"uf": r["uf"], "estoque_total": num(r["estoque_total"]), "num_instituicoes": r["num_instituicoes"]}
                               for r in m.estoque_por_uf(catmat_id)],
            "evolucao_preco": [{"data": str(r["data_de_compra"])[:10], "preco_medio": round(num(r["preco_medio"]), 4)}
                               for r in m.evolucao_preco_compra(catmat_id)],
            "fornecedores_top": [{"nome": r["nome_fornecedor"], "valor_total": num(r["valor_total"])} for r in m.compras_por_fornecedor(catmat_id, 15)],
            "fabricantes_top": [{"nome": r["nome_fabricante"], "valor_total": num(r["valor_total"])} for r in m.compras_por_fabricante(catmat_id, 15)],
        },
    }


def main() -> None:
    question = sys.argv[1]
    catmat = int(sys.argv[2]) if len(sys.argv) > 2 else None
    ctx = ui_context(catmat)
    tok = requests.post(f"{URL}/auth/token", json={"clientId": os.environ["AUTODRIVE_AUTH_CLIENT_ID"],
                                                  "clientSecret": os.environ["AUTODRIVE_AUTH_CLIENT_SECRET"]}, timeout=30).json()["accessToken"]
    h = {"Authorization": f"Bearer {tok}", "Origin": ORIGIN, "X-AutoDrive-Client": MANIFEST["client"], "X-AutoDrive-Environment": "stg"}
    base = f"{URL}/datasets/{MANIFEST['dataset_id']}/ai-question"
    body = {"question": question, "assistant_id": MANIFEST["assistant_id"], "ui_context": ctx,
            "user_context": {"user_id": "embrapii-demo-user", "tenant_id": "dadosferademo", "role": "analista de saúde pública (demo)"},
            "external_user_id": "embrapii-demo-user", "language": "pt-BR"}
    r = requests.post(base, json=body, headers=h, timeout=120)
    r.raise_for_status()
    qid = r.json().get("question_id") or r.json().get("id")
    t0 = time.time()
    while True:
        res = requests.get(f"{base}/{qid}", headers=h, timeout=60).json()
        if res.get("status") in ("success", "failed", "error", "completed") or time.time() - t0 > 240:
            break
        time.sleep(3)
    out = ROOT / "autodrive" / "last_ai_question.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str))
    result = res.get("result") or res
    print("status:", res.get("status"), f"({time.time() - t0:.0f}s)")
    print((result.get("answer") or res.get("answer") or "")[:2500])
    for b in result.get("response_blocks") or []:
        print("BLOCK", b.get("type"), b.get("chart_type"), b.get("title"), "x=", b.get("x_key"), "y=", b.get("y_key"), "n=", len(b.get("data") or []))


if __name__ == "__main__":
    main()
