"""Chat Autodrive embutido no app: token do widget, config pública e proxy same-origin para a Assistant API.

Mesmo contrato do demo-lakehouse-porto (api/routers/autodrive.py) e do template-autodrive-chatbot-integration:
- POST /api/autodrive/chat-token troca AUTODRIVE_AUTH_CLIENT_ID/SECRET (só no servidor) por um token curto e devolve
  {access_token, token_type, expires_in} (snake_case) ao widget;
- GET /api/autodrive/config diz ao front qual assistente/KB usar;
- /api/autodrive/proxy/{path} repassa as chamadas do widget server-to-server. A allowlist de Origin da Assistant API é
  uma env do cluster do Autodrive e não inclui o host do demo2; usamos um origin já liberado (AUTODRIVE_PROXY_ORIGIN).
  Na volta, as respostas de ai-question são ajustadas ao que o widget do STG sabe desenhar (ver _normalizar_resposta).
"""

import json
import os
import re
from typing import Any, Dict

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/api/autodrive", tags=["Autodrive"])

AUTODRIVE_URL = os.getenv("AUTODRIVE_URL", "https://autodrive-assistant-api-standalone.stg.dadosfera.ai").rstrip("/")
PROXY_ORIGIN = os.getenv("AUTODRIVE_PROXY_ORIGIN", "https://app-intelligence-dadosferademo.dadosfera.ai")
_HOP_BY_HOP = {"host", "content-length", "connection", "accept-encoding", "origin", "referer", "cookie"}

# O widget do STG só conhece "horizontal_bar"; a API às vezes emite "bar_horizontal" e o bloco vira
# "Resposta recebida sem conteúdo renderizável" (mesmo bug visto no Porto).
_CHART_TYPE_ALIASES = {"bar_horizontal": "horizontal_bar", "donut": "pie", "stacked_bar": "bar"}
# O modelo às vezes repete o gráfico no texto (JSON em <chart-plus-json> ou uma imagem markdown inventada).
_LIXO_NO_TEXTO = [
    re.compile(r"<chart-plus-json>.*?</chart-plus-json>", re.DOTALL | re.IGNORECASE),
    re.compile(r"!\[[^\]]*\]\([^)]*\)"),
]


@router.post("/chat-token")
def chat_token() -> Dict[str, Any]:
    cid, secret = os.getenv("AUTODRIVE_AUTH_CLIENT_ID"), os.getenv("AUTODRIVE_AUTH_CLIENT_SECRET")
    if not cid or not secret:
        raise HTTPException(500, "AUTODRIVE_AUTH_CLIENT_ID/SECRET não configurados no serviço")
    try:
        r = requests.post(f"{AUTODRIVE_URL}/auth/token", json={"clientId": cid, "clientSecret": secret}, timeout=15)
    except requests.RequestException as exc:
        raise HTTPException(502, f"falha ao falar com o Autodrive: {exc}") from exc
    if r.status_code >= 400:
        raise HTTPException(502, f"Autodrive recusou as credenciais ({r.status_code})")
    body = r.json()
    token = body.get("accessToken") or body.get("access_token")
    if not token:
        raise HTTPException(502, "resposta do Autodrive sem token")
    return {
        "access_token": token,
        "token_type": body.get("tokenType") or body.get("token_type") or "Bearer",
        "expires_in": body.get("expiresIn") or body.get("expires_in") or 300,
    }


@router.get("/config")
def config() -> Dict[str, Any]:
    dataset_id, assistant_id = os.getenv("AUTODRIVE_DATASET_ID", ""), os.getenv("AUTODRIVE_ASSISTANT_ID", "")
    return {
        "enabled": bool(dataset_id and assistant_id and os.getenv("AUTODRIVE_AUTH_CLIENT_ID")),
        "widget_host": os.getenv("AUTODRIVE_WIDGET_HOST", "https://autodrive-standalone.stg.dadosfera.ai"),
        "client": os.getenv("AUTODRIVE_CLIENT", "dadosfera-stg"),
        "environment": os.getenv("AUTODRIVE_ENVIRONMENT", "stg"),
        "dataset_id": dataset_id,
        "assistant_id": assistant_id,
        "title": os.getenv("AUTODRIVE_TITLE", "EMBRAPII · Analista DATASUS"),
    }


def _normalizar_resposta(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    for bloco in payload.get("response_blocks") or []:
        if isinstance(bloco, dict) and bloco.get("chart_type") in _CHART_TYPE_ALIASES:
            bloco["chart_type"] = _CHART_TYPE_ALIASES[bloco["chart_type"]]
    answer = payload.get("answer")
    if isinstance(answer, str) and payload.get("response_blocks"):
        for padrao in _LIXO_NO_TEXTO:
            answer = padrao.sub("", answer)
        payload["answer"] = re.sub(r"\n{3,}", "\n\n", answer).strip()
    if isinstance(payload.get("result"), dict):
        payload["result"] = _normalizar_resposta(payload["result"])
    return payload


@router.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request) -> Response:
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP_BY_HOP}
    headers["Origin"] = PROXY_ORIGIN
    body = await request.body()
    try:
        r = await run_in_threadpool(  # requests é síncrono: fora do event loop
            requests.request,
            request.method, f"{AUTODRIVE_URL}/{path}", params=dict(request.query_params),
            data=body or None, headers=headers, timeout=180,
        )
    except requests.RequestException as exc:
        raise HTTPException(502, f"proxy Autodrive: {exc}") from exc
    content = r.content
    media_type = r.headers.get("content-type")
    if request.method == "GET" and "/ai-question/" in f"/{path}" and r.ok and "json" in (media_type or ""):
        content = json.dumps(_normalizar_resposta(r.json()), ensure_ascii=False).encode("utf-8")
    return Response(content=content, status_code=r.status_code, media_type=media_type)
