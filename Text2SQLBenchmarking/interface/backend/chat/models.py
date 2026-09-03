from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from interface.backend.domain.capabilities import ConfigurationSelection
from interface.backend.domain.errors import PublicErrorCode, public_error


class ChatJobState(str, Enum):
    ACCEPTED = "accepted"
    LOADING_MODEL = "loading_model"
    GENERATING = "generating"
    VALIDATING_SQL = "validating_sql"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EXPIRED = "expired"


TERMINAL = {ChatJobState.SUCCEEDED, ChatJobState.FAILED, ChatJobState.EXPIRED}


@dataclass(frozen=True)
class ChatError:
    code: PublicErrorCode | str
    message: str
    retryable: bool | None = None

    def __post_init__(self) -> None:
        payload = public_error(self.code, self.message, self.retryable)
        object.__setattr__(self, "code", payload.code.value)
        object.__setattr__(self, "message", payload.message)
        object.__setattr__(self, "retryable", payload.retryable)

    def as_dict(self) -> dict[str, Any]:
        return {"code": str(self.code), "message": self.message, "retryable": bool(self.retryable)}


@dataclass(frozen=True)
class ChatJobSnapshot:
    job_id: str
    configuration: ConfigurationSelection
    state: ChatJobState
    created_at: str
    sql: str | None = None
    columns: tuple[str, ...] | None = None
    rows: tuple[tuple[Any, ...], ...] | None = None
    row_count: int | None = None
    displayed_row_count: int | None = None
    truncated: bool | None = None
    generation_time_seconds: float | None = None
    execution_time_seconds: float | None = None
    error: ChatError | None = None

    @classmethod
    def accepted(cls, configuration: ConfigurationSelection) -> "ChatJobSnapshot":
        return cls(str(uuid4()), configuration, ChatJobState.ACCEPTED, datetime.now(timezone.utc).isoformat())

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id, "configuration": self.configuration.__dict__, "state": self.state.value,
            "created_at": self.created_at, "sql": self.sql, "columns": list(self.columns) if self.columns is not None else None,
            "rows": [list(row) for row in self.rows] if self.rows is not None else None,
            "rowCount": self.row_count, "displayedRowCount": self.displayed_row_count,
            "truncated": self.truncated, "generationTimeSeconds": self.generation_time_seconds,
            "executionTimeSeconds": self.execution_time_seconds, "error": self.error.as_dict() if self.error else None,
        }

    def update(self, **values: Any) -> "ChatJobSnapshot":
        return replace(self, **values)
