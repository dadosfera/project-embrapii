"""Tradução centralizada de erros de domínio para envelopes HTTP seguros."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from interface.backend.benchmark.artifacts import BenchmarkArtifactError
from interface.backend.benchmark.journal import BenchmarkJournalError
from interface.backend.benchmark.service import BenchmarkServiceError
from interface.backend.benchmark.reexecution import ReexecutionIntentError
from interface.backend.operations import OperationCoordinatorError
from interface.backend.runtime import (
    RuntimeKeyError,
    RuntimeManagerError,
    RuntimeManagerErrorCode,
)
from interface.backend.diagnostics import log_diagnostic_event
from interface.backend.domain.errors import (
    PublicErrorCode,
    classify_model_load_error,
    http_status_for,
    public_error,
)


@dataclass(frozen=True)
class ApiError(Exception):
    code: str
    message: str
    status_code: int | None = None
    retryable: bool | None = None


def _response(
    code: PublicErrorCode | str,
    message: str | None = None,
    status: int | None = None,
    retryable: bool | None = None,
) -> JSONResponse:
    payload = public_error(code, message, retryable)
    return JSONResponse(
        status_code=status if status is not None else http_status_for(payload.code),
        content={"error": payload.as_dict()},
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _response(exc.code, exc.message, exc.status_code, exc.retryable)

    @app.exception_handler(OperationCoordinatorError)
    async def operation_error(_: Request, exc: OperationCoordinatorError) -> JSONResponse:
        return _response(exc.code.value, exc.public_message)

    @app.exception_handler(BenchmarkJournalError)
    async def journal_error(_: Request, exc: BenchmarkJournalError) -> JSONResponse:
        return _response(exc.code.value, exc.public_message)

    @app.exception_handler(BenchmarkServiceError)
    async def benchmark_error(_: Request, exc: BenchmarkServiceError) -> JSONResponse:
        return _response(exc.code.value, exc.public_message, retryable=exc.retryable)

    @app.exception_handler(ReexecutionIntentError)
    async def reexecution_error(_: Request, exc: ReexecutionIntentError) -> JSONResponse:
        return _response(exc.code.value, exc.public_message)

    @app.exception_handler(BenchmarkArtifactError)
    async def artifact_error(_: Request, exc: BenchmarkArtifactError) -> JSONResponse:
        return _response(exc.code, exc.public_message)

    @app.exception_handler(RuntimeKeyError)
    async def runtime_key_error(_: Request, exc: RuntimeKeyError) -> JSONResponse:
        return _response(PublicErrorCode.UNSUPPORTED_COMBINATION, exc.public_message)

    @app.exception_handler(RuntimeManagerError)
    async def runtime_manager_error(_: Request, exc: RuntimeManagerError) -> JSONResponse:
        if exc.code is RuntimeManagerErrorCode.RUNTIME_LOAD_ERROR:
            payload = classify_model_load_error(exc).error
        elif exc.code is RuntimeManagerErrorCode.RUNTIME_TOKEN_MISMATCH:
            payload = public_error(PublicErrorCode.UNSUPPORTED_COMBINATION)
        else:
            payload = public_error(PublicErrorCode.INTERNAL_ERROR)
        log_diagnostic_event(
            "api.runtime_manager_error",
            exception=exc,
            error_code=payload.code.value,
            runtime_error_code=exc.code.value,
        )
        return _response(payload.code, payload.message, retryable=payload.retryable)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
        return _response(PublicErrorCode.INVALID_REQUEST)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        log_diagnostic_event(
            "api.unexpected_error",
            exception=exc,
            method=request.method,
            route=request.url.path,
        )
        return _response(PublicErrorCode.INTERNAL_ERROR)
