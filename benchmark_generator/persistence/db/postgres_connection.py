import logging
from typing import Any, Mapping, Iterable
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from benchmark_generator.persistence.db.database_connection import DatabaseConnection


class PostgresConnection(DatabaseConnection):
    def __init__(
        self,
        *,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
    ):
        self._dsn = (
            f"host={host} "
            f"port={port} "
            f"dbname={database} "
            f"user={user} "
            f"password={password}"
        )
        self._conn: psycopg.Connection | None = None
        self.logger = logging.getLogger("PostgresConnection")

    def connect(self) -> None:
        if self._conn is None:
            self._conn = psycopg.connect(
                self._dsn,
                row_factory=dict_row
            )
            self.logger.info("Connected to PostgreSQL database: %s", self._conn)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def execute(
        self,
        query: str,
        params: Mapping[str, Any] | None = None
    ) -> None:
        assert self._conn is not None, "Connection not initialized"
        with self._conn.cursor() as cur:
            cur.execute(query, params)

    def fetch_one(
        self,
        query: str,
        params: Mapping[str, Any] | None = None
    ) -> Mapping[str, Any] | None:
        assert self._conn is not None, "Connection not initialized"
        with self._conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetch_all(
        self,
        query: str,
        params: Mapping[str, Any] | None = None
    ) -> Iterable[Mapping[str, Any]]:
        assert self._conn is not None, "Connection not initialized"
        with self._conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    @contextmanager
    def transaction(self):
        assert self._conn is not None, "Connection not initialized"
        try:
            yield self
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def rollback(self) -> None:
        assert self._conn is not None, "Connection not initialized"
        self._conn.rollback()

    def commit(self) -> None:
        assert self._conn is not None, "Connection not initialized"
        self._conn.commit()
