import os
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


def get_connection():
    """
    Abre uma conexão com o PostgreSQL através do túnel SSH local.

    A sessão é configurada como somente leitura para reduzir o risco
    de alterações acidentais no banco.
    """
    required_variables = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing_variables = [
        variable
        for variable in required_variables
        if not os.getenv(variable)
    ]

    if missing_variables:
        raise RuntimeError(
            "Variáveis ausentes no arquivo .env: "
            + ", ".join(missing_variables)
        )

    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5,
        row_factory=dict_row,
        options="-c default_transaction_read_only=on",
    )


def fetch_all(query: str, params: dict[str, Any] | None = None) -> list[dict]:
    """Executa um SELECT e retorna todas as linhas como dicionários."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or {})
            return cursor.fetchall()


def fetch_one(query: str, params: dict[str, Any] | None = None) -> dict | None:
    """Executa um SELECT e retorna uma única linha como dicionário."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or {})
            return cursor.fetchone()