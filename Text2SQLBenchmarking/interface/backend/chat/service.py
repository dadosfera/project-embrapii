from __future__ import annotations

import os
from time import monotonic
from typing import Callable

from interface.backend.domain.capabilities import ApplicationMode, ConfigurationSelection
from interface.backend.diagnostics import log_diagnostic_event
from interface.backend.domain.errors import (
    PublicErrorCode,
    classify_loading_model_error,
    classify_query_execution_error,
    public_error,
)
from interface.backend.operations import ExclusiveOperationService
from interface.backend.runtime import RuntimeKey

from .jobs import ChatJobs
from .models import ChatError, ChatJobSnapshot, ChatJobState
from .query import ChatServiceError, QueryExecutor, QueryResult, safe_database_value
from .sql_guard import UnsafeSqlError, approve_read_only
from .sql_normalizer import SqlNormalizationError, normalize_sql_output


class ChatService:
    def __init__(self, *, operations: ExclusiveOperationService, jobs: ChatJobs, query_executor: QueryExecutor | None = None, clock: Callable[[], float] = monotonic) -> None:
        self._operations = operations
        self._jobs = jobs
        if query_executor is None:
            # The concrete database integration is an adapter and is imported lazily.
            from interface.backend.adapters.postgres_chat import PostgreSqlChatExecutor
            query_executor = PostgreSqlChatExecutor()
        self._query_executor = query_executor
        self._clock = clock

    def get(self, job_id: str) -> ChatJobSnapshot | None:
        return self._jobs.get(job_id)

    def run(self, question: str, configuration: ConfigurationSelection, *, on_accepted: Callable[[ChatJobSnapshot], None]) -> ChatJobSnapshot:
        snapshot = ChatJobSnapshot.accepted(configuration)
        key = RuntimeKey.from_configuration(configuration, ApplicationMode.CHAT, random_seed=42, hf_token=os.getenv("HF_TOKEN"))
        generation_started: float | None = None

        def admitted() -> None:
            self._jobs.add(snapshot)
            on_accepted(snapshot)
            self._jobs.update(snapshot.job_id, state=ChatJobState.LOADING_MODEL)

        def generating() -> None:
            nonlocal generation_started
            self._jobs.update(snapshot.job_id, state=ChatJobState.GENERATING)
            generation_started = self._clock()

        def execute_generated(sql: str) -> tuple[float, float, QueryResult, str]:
            if generation_started is None:
                raise ChatServiceError(PublicErrorCode.INTERNAL_ERROR)
            generation_seconds = self._clock() - generation_started
            try:
                generated_sql = normalize_sql_output(sql)
            except SqlNormalizationError as exc:
                raise ChatServiceError(
                    PublicErrorCode.SQL_GENERATION_ERROR,
                    "O modelo não gerou uma consulta SQL válida.",
                ) from exc
            self._jobs.update(snapshot.job_id, state=ChatJobState.VALIDATING_SQL, sql=generated_sql, generation_time_seconds=generation_seconds)
            try:
                approved = approve_read_only(generated_sql)
            except UnsafeSqlError as exc:
                raise ChatServiceError(PublicErrorCode.UNSAFE_SQL) from exc
            self._jobs.update(snapshot.job_id, state=ChatJobState.EXECUTING)
            execution_started = self._clock()
            result = self._query_executor.execute(configuration, approved)
            execution_seconds = self._clock() - execution_started
            return generation_seconds, execution_seconds, result, approved

        try:
            generation_seconds, execution_seconds, result, approved = self._operations.run_chat(key, hf_token=os.getenv("HF_TOKEN"), question=question, callback=execute_generated, on_acquired=admitted, on_generating=generating)
            return self._jobs.update(snapshot.job_id, state=ChatJobState.SUCCEEDED, sql=approved, columns=result.columns, rows=result.displayed_rows, row_count=result.row_count, displayed_row_count=result.displayed_row_count, truncated=result.truncated, generation_time_seconds=generation_seconds, execution_time_seconds=execution_seconds)
        except ChatServiceError as exc:
            return self._jobs.update(snapshot.job_id, state=ChatJobState.FAILED, error=ChatError(exc.code, exc.public_message, exc.retryable))
        except Exception as exc:
            current = self._jobs.get(snapshot.job_id)
            if current is None:
                raise
            state = current.state
            if state is ChatJobState.LOADING_MODEL:
                payload = classify_loading_model_error(exc)
            elif state is ChatJobState.GENERATING:
                payload = public_error(PublicErrorCode.SQL_GENERATION_ERROR)
            elif state is ChatJobState.EXECUTING:
                payload = classify_query_execution_error(exc)
            else:
                payload = public_error(PublicErrorCode.INTERNAL_ERROR)
            log_diagnostic_event(
                "chat.job.failed",
                exception=exc,
                stage=state.value,
                error_code=payload.code.value,
                job_id=snapshot.job_id,
            )
            return self._jobs.update(
                snapshot.job_id,
                state=ChatJobState.FAILED,
                error=ChatError(payload.code, payload.message, payload.retryable),
            )
