from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

ENGINES = ("postgres", "snowflake")


class DatabaseError(Exception):
    """Falha de banco, independente do engine."""


class Q:
    """SQL com uma versão por engine. `pg` é o texto original do Postgres."""

    def __init__(self, pg: str, sf: Optional[str] = None) -> None:
        self.pg = pg
        self.sf = sf

    def for_engine(self, engine: str) -> str:
        if engine == "postgres":
            return self.pg
        if self.sf is None:
            raise NotImplementedError("query sem versão Snowflake")
        return self.sf


def get_engine() -> str:
    engine = os.getenv("DB_ENGINE", "postgres").strip().lower()
    if engine not in ENGINES:
        raise RuntimeError(f"DB_ENGINE inválido: {engine!r} (use postgres ou snowflake)")
    return engine


_COMMENT = re.compile(r"(--[^\n]*\n)|(/\*.*?\*/)", re.S)


def _assert_read_only(sql: str) -> None:
    head = _COMMENT.sub("\n", sql).lstrip().split(None, 1)
    if not head or head[0].upper() not in ("SELECT", "WITH"):
        raise ValueError("Somente SELECT/WITH são permitidos.")


def get_connection():
    """Conexão Postgres somente leitura (usada também pelo /health/database)."""
    import psycopg
    from psycopg.rows import dict_row

    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise RuntimeError("Variáveis ausentes no arquivo .env: " + ", ".join(missing))
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"), dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), connect_timeout=5,
        row_factory=dict_row, options="-c default_transaction_read_only=on",
    )


def _run(engine: str, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    if engine == "postgres":
        import psycopg

        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    return list(cursor.fetchall())
        except psycopg.Error as exc:
            raise DatabaseError(str(exc)) from exc
    from backend import snowflake_conn

    try:
        return snowflake_conn.run(sql, params)
    except Exception as exc:
        raise DatabaseError(str(exc)) from exc


def _execute(query: Union[str, Q], params: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from backend.cache import query_cache

    q = query if isinstance(query, Q) else Q(pg=query)
    engine = get_engine()
    sql = q.for_engine(engine)
    _assert_read_only(sql)
    p = params or {}
    key = (engine, sql, tuple(sorted((k, str(v)) for k, v in p.items())))

    def load() -> List[Dict[str, Any]]:
        rows = _run(engine, sql, p)
        return [{str(k).lower(): v for k, v in row.items()} for row in rows]

    return query_cache.get_or_load(key, load)


def fetch_all(query: Union[str, Q], params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Executa um SELECT e retorna todas as linhas como dicionários."""
    return _execute(query, params)


def fetch_one(query: Union[str, Q], params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Executa um SELECT e retorna uma única linha como dicionário."""
    rows = _execute(query, params)
    return rows[0] if rows else None
