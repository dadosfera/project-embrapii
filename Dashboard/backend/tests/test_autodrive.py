from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.api import autodrive
from backend.main import app

client = TestClient(app)


def _resp(status=200, body=None, content_type="application/json"):
    r = MagicMock()
    r.status_code, r.ok = status, status < 400
    r.json.return_value = body or {}
    r.content = b"{}" if body is None else __import__("json").dumps(body).encode()
    r.headers = {"content-type": content_type}
    return r


def test_chat_token_converte_para_snake_case(monkeypatch):
    monkeypatch.setenv("AUTODRIVE_AUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("AUTODRIVE_AUTH_CLIENT_SECRET", "sec")
    with patch.object(autodrive.requests, "post", return_value=_resp(body={"accessToken": "t", "tokenType": "Bearer", "expiresIn": 300})) as p:
        r = client.post("/api/autodrive/chat-token")
    assert r.status_code == 200
    assert r.json() == {"access_token": "t", "token_type": "Bearer", "expires_in": 300}
    assert p.call_args.kwargs["json"] == {"clientId": "cid", "clientSecret": "sec"}


def test_chat_token_sem_credenciais(monkeypatch):
    monkeypatch.delenv("AUTODRIVE_AUTH_CLIENT_ID", raising=False)
    monkeypatch.delenv("AUTODRIVE_AUTH_CLIENT_SECRET", raising=False)
    assert client.post("/api/autodrive/chat-token").status_code == 500


def test_config_nao_expoe_secret(monkeypatch):
    monkeypatch.setenv("AUTODRIVE_AUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("AUTODRIVE_AUTH_CLIENT_SECRET", "segredo-que-nao-pode-vazar")
    monkeypatch.setenv("AUTODRIVE_DATASET_ID", "ds")
    monkeypatch.setenv("AUTODRIVE_ASSISTANT_ID", "as")
    r = client.get("/api/autodrive/config")
    assert r.json()["enabled"] is True
    assert "segredo-que-nao-pode-vazar" not in r.text and "cid" not in r.text


def test_normaliza_chart_type_e_limpa_texto():
    payload = {
        "answer": "Resumo.\n<chart-plus-json>\n{\"a\": 1}\n</chart-plus-json>\n![chart](https://x/y.png)\nFim.",
        "response_blocks": [{"type": "chart", "chart_type": "bar_horizontal"}, {"type": "chart", "chart_type": "line"}],
    }
    out = autodrive._normalizar_resposta(payload)
    assert [b["chart_type"] for b in out["response_blocks"]] == ["horizontal_bar", "line"]
    assert "chart-plus-json" not in out["answer"] and "![" not in out["answer"]
    assert out["answer"].startswith("Resumo.") and out["answer"].endswith("Fim.")


def test_texto_sem_blocos_fica_intacto():
    payload = {"answer": "![logo](x.png)", "response_blocks": []}
    assert autodrive._normalizar_resposta(payload)["answer"] == "![logo](x.png)"


def test_proxy_troca_origin_e_normaliza_poll():
    body = {"status": "success", "answer": "ok", "response_blocks": [{"type": "chart", "chart_type": "bar_horizontal"}]}
    with patch.object(autodrive.requests, "request", return_value=_resp(body=body)) as req:
        r = client.get("/api/autodrive/proxy/datasets/ds/ai-question/q1", headers={"Authorization": "Bearer t", "Origin": "https://evil"})
    assert r.status_code == 200
    assert r.json()["response_blocks"][0]["chart_type"] == "horizontal_bar"
    args, kwargs = req.call_args
    assert args[1].endswith("/datasets/ds/ai-question/q1")
    assert kwargs["headers"]["Origin"] == autodrive.PROXY_ORIGIN
    assert kwargs["headers"]["authorization"] == "Bearer t"
