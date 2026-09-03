"""PostgreSQL execution adapter for Chat queries."""
from __future__ import annotations

from typing import Any, Callable

from interface.backend.chat.query import (
    ChatServiceError,
    QueryResult,
    safe_database_value,
)
from interface.backend.domain.capabilities import ConfigurationSelection
from interface.backend.domain.errors import classify_query_execution_error


class PostgreSqlChatExecutor:
    def __init__(
        self,
        *,
        timeout_ms: int = 15_000,
        connect: Callable[..., Any] | None = None,
        config_resolver: Callable[[str], tuple[dict[str, Any], Any]] | None = None,
    ) -> None:
        self._timeout_ms = timeout_ms
        self._connect = connect
        self._config_resolver = config_resolver

    def execute(self, configuration: ConfigurationSelection, sql: str) -> QueryResult:
        connection = None
        cursor = None
        try:
            connect = self._resolve_connect()
            resolver = self._resolve_config_resolver()
            config, _ = resolver(configuration.database)
            connection = connect(
                user=config["user"],
                password=config["password"],
                host=config["host"],
                port=config["port"],
                dbname=config["db_name"],
            )
            connection.set_session(readonly=True, autocommit=False)
            cursor = connection.cursor()
            cursor.execute("SET LOCAL statement_timeout = %s", (self._timeout_ms,))
            cursor.execute(sql)
            rows = cursor.fetchmany(201)
            return QueryResult(
                columns=tuple(item[0] for item in cursor.description or ()),
                displayed_rows=tuple(
                    tuple(safe_database_value(value) for value in row)
                    for row in rows[:200]
                ),
                row_count=len(rows),
                displayed_row_count=min(len(rows), 200),
                truncated=len(rows) > 200,
            )
        except Exception as exc:
            raise _classify_postgres_error(exc) from exc
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
            if connection is not None:
                try:
                    connection.rollback()
                except Exception:
                    pass
                try:
                    connection.close()
                except Exception:
                    pass

    def _resolve_connect(self) -> Callable[..., Any]:
        if self._connect is not None:
            return self._connect
        import psycopg2

        return psycopg2.connect

    def _resolve_config_resolver(self) -> Callable[[str], tuple[dict[str, Any], Any]]:
        if self._config_resolver is not None:
            return self._config_resolver
        from src.utilitis import get_db_config

        return get_db_config


def _classify_postgres_error(exc: Exception) -> ChatServiceError:
    payload = classify_query_execution_error(exc)
    return ChatServiceError(payload.code, payload.message, payload.retryable)
