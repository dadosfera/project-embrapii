"""Conexão Snowflake do dadosferademo.

Credenciais: SNOWFLAKE_SECRET_FILE (JSON local) ou SNOWFLAKE_SECRET_ID (AWS Secrets Manager, dentro do
Módulo de Inteligência). Credenciais AWS temporárias expiradas são descartadas para o boto3 cair no role do nó.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict

_lock = threading.Lock()
_conn = None
STALE = ("390114", "390111", "Session no longer exists", "connection is closed", "251005",
         "Authentication token has expired")


def _secret() -> Dict[str, Any]:
    f = os.getenv("SNOWFLAKE_SECRET_FILE")
    if f and Path(f).exists():
        return json.loads(Path(f).read_text())
    import boto3

    sid = os.environ["SNOWFLAKE_SECRET_ID"]

    def get() -> str:
        client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "us-east-1"))
        return client.get_secret_value(SecretId=sid)["SecretString"]

    try:
        raw = get()
    except Exception as exc:
        if "ExpiredToken" not in str(exc):
            raise
        for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
            os.environ.pop(k, None)
        raw = get()
    return json.loads(raw)


def _connect():
    import snowflake.connector
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    sec = _secret()
    account = f"{sec['account']}.{sec['region']}" if sec.get("region") else sec["account"]
    cfg: Dict[str, Any] = {
        "user": sec["username"], "account": account, "role": sec.get("role"),
        "warehouse": sec.get("warehouse"),
        "database": os.getenv("SNOWFLAKE_DATABASE") or sec.get("database"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "EMBRAPII_DATASUS"),
        "paramstyle": "pyformat", "login_timeout": 20, "network_timeout": 60,
    }
    if sec.get("private_key"):
        pk = serialization.load_pem_private_key(sec["private_key"].encode(), password=None,
                                                backend=default_backend())
        cfg["private_key"] = pk.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                                              serialization.NoEncryption())
    else:
        cfg["password"] = sec["password"]
    return snowflake.connector.connect(**{k: v for k, v in cfg.items() if v})


def run(sql: str, params: Dict[str, Any]):
    """Executa e devolve lista de dicts. Reconecta uma vez se a sessão expirou."""
    global _conn

    def once():
        with _conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    with _lock:
        if _conn is None:
            _conn = _connect()
        try:
            return once()
        except Exception as exc:
            if not any(m in str(exc) for m in STALE):
                raise
            try:
                _conn.close()
            except Exception:
                pass
            _conn = _connect()
            return once()
