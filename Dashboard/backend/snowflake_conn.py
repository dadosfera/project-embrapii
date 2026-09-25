"""Conexão Snowflake do dadosferademo.

Credenciais: SNOWFLAKE_SECRET_FILE (JSON local) ou SNOWFLAKE_SECRET_ID (AWS Secrets Manager, dentro do
Módulo de Inteligência). O secret fica em memória após a primeira leitura, então reconectar ao Snowflake não
depende da AWS. Se as credenciais AWS temporárias do serviço expiraram, elas são descartadas e a nova tentativa usa
uma sessão boto3 nova (a sessão padrão guarda a credencial resolvida na primeira chamada), caindo no role do nó.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict

_lock = threading.Lock()
_conn = None
_secret_cache = None
STALE = ("390114", "390111", "session no longer exists", "connection is closed", "251005",
         "authentication token has expired", "250002")


def _secret() -> Dict[str, Any]:
    global _secret_cache
    if _secret_cache is not None:
        return _secret_cache
    f = os.getenv("SNOWFLAKE_SECRET_FILE")
    if f:
        path = Path(f)
        if not path.exists():
            raise RuntimeError(f"SNOWFLAKE_SECRET_FILE não encontrado: {f}")
        _secret_cache = json.loads(path.read_text())
        return _secret_cache

    sid = os.getenv("SNOWFLAKE_SECRET_ID")
    if not sid:
        raise RuntimeError(
            "Defina SNOWFLAKE_SECRET_FILE (JSON local) ou SNOWFLAKE_SECRET_ID (AWS Secrets Manager)."
        )
    import boto3.session

    def get() -> str:
        client = boto3.session.Session().client("secretsmanager", region_name=os.getenv("AWS_REGION", "us-east-1"))
        return client.get_secret_value(SecretId=sid)["SecretString"]

    try:
        raw = get()
    except Exception as exc:
        if "ExpiredToken" not in str(exc):
            raise
        for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_SECURITY_TOKEN"):
            os.environ.pop(k, None)
        raw = get()
    _secret_cache = json.loads(raw)
    return _secret_cache


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
        # mesmo fuso do Postgres da UFMG (Etc/UTC): TIMESTAMP_LTZ::date e isoformat batem com o PG
        "timezone": "UTC",
    }
    if sec.get("private_key"):
        pk = serialization.load_pem_private_key(sec["private_key"].encode(), password=None,
                                                backend=default_backend())
        cfg["private_key"] = pk.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                                              serialization.NoEncryption())
    else:
        cfg["password"] = sec["password"]
    return snowflake.connector.connect(**{k: v for k, v in cfg.items() if v})


def _is_stale(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker.lower() in text for marker in STALE)


def _get_conn():
    """Devolve a conexão ativa, abrindo uma se preciso. Só a criação/troca é protegida pelo lock."""
    global _conn
    with _lock:
        if _conn is None:
            _conn = _connect()
        return _conn


def _reconnect(failed):
    """Substitui `failed` por uma conexão nova, com compare-and-swap sob o lock.

    Várias threads podem ver a mesma conexão expirar ao mesmo tempo; só a primeira a
    entrar no lock deve fechá-la e reconectar. Se, quando uma thread entra no lock,
    `_conn` já não é mais `failed` (outra thread já trocou), ela reaproveita a conexão
    nova em vez de fechá-la e abrir outra. Se `_connect()` falhar, `_conn` fica `None`
    para que a próxima chamada tente reconectar de novo, em vez de reusar algo quebrado.
    """
    global _conn
    with _lock:
        if _conn is not None and _conn is not failed:
            # outra thread já reconectou nesse meio-tempo: reusa o que ela abriu.
            return _conn
        if failed is not None:
            try:
                failed.close()
            except Exception:
                pass
        _conn = None
        _conn = _connect()
        return _conn


def run(sql: str, params: Dict[str, Any]):
    """Executa e devolve lista de dicts. Reconecta uma vez se a sessão expirou."""

    def once(conn):
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    conn = _get_conn()
    try:
        return once(conn)
    except Exception as exc:
        if not _is_stale(exc):
            raise
        conn = _reconnect(conn)
        return once(conn)
