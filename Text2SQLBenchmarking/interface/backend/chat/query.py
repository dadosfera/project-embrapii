"""Neutral contracts shared by the Chat service and database adapters."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Protocol
from uuid import UUID

from interface.backend.domain.capabilities import ConfigurationSelection
from interface.backend.domain.errors import PublicErrorCode, public_error


class ChatServiceError(RuntimeError):
    def __init__(
        self,
        code: PublicErrorCode | str,
        message: str | None = None,
        retryable: bool | None = None,
    ) -> None:
        payload = public_error(code, message, retryable)
        super().__init__(payload.message)
        self.code = payload.code.value
        self.public_message = payload.message
        self.retryable = payload.retryable


@dataclass(frozen=True)
class QueryResult:
    columns: tuple[str, ...]
    displayed_rows: tuple[tuple[Any, ...], ...]
    row_count: int
    displayed_row_count: int
    truncated: bool


class QueryExecutor(Protocol):
    def execute(self, configuration: ConfigurationSelection, sql: str) -> QueryResult: ...


def safe_database_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bytes):
        return "[binary data]"
    if isinstance(value, Enum):
        return safe_database_value(value.value)
    return "[unsupported value]"
