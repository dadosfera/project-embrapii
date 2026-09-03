from __future__ import annotations

import errno
import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from interface.backend.api.errors import install_error_handlers
from interface.backend.api.app import create_app
from interface.backend.tests.test_api_health import api_container
from interface.backend.chat.jobs import ChatJobs
from interface.backend.chat.models import ChatJobState
from interface.backend.chat.query import QueryResult
from interface.backend.chat.service import ChatService
from interface.backend.domain.capabilities import ConfigurationSelection
from interface.backend.operations import (
    OperationCoordinatorError,
    OperationErrorCode,
    OperationType,
)
from interface.backend.runtime import (
    RuntimeKeyError,
    RuntimeManagerError,
    RuntimeManagerErrorCode,
)


CONFIG = ConfigurationSelection(
    "sih_database",
    "raw_model",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    "default",
)


def _raise_wrapped(root: BaseException) -> None:
    try:
        raise root
    except BaseException as cause:
        raise RuntimeManagerError(
            RuntimeManagerErrorCode.RUNTIME_LOAD_ERROR,
            "safe runtime failure",
            "safe detail",
        ) from cause


class LoadingFailureOperations:
    def __init__(self, error: BaseException) -> None:
        self.error = error

    def run_chat(self, _key, *, on_acquired, **_kwargs):
        on_acquired()
        _raise_wrapped(self.error)


class GeneratingFailureOperations:
    def run_chat(self, _key, *, on_acquired, on_generating, **_kwargs):
        on_acquired()
        on_generating()
        raise RuntimeError("raw model output token=secret")


class SuccessfulOperations:
    def run_chat(self, _key, *, on_acquired, on_generating, callback, **_kwargs):
        on_acquired()
        on_generating()
        return callback("SELECT 1")


class ErrorExecutor:
    def __init__(self, error: BaseException) -> None:
        self.error = error

    def execute(self, _configuration, _sql):
        raise self.error


class PgError(RuntimeError):
    def __init__(self, sqlstate: str | None, message: str = "synthetic database failure") -> None:
        super().__init__(message)
        self.pgcode = sqlstate


def _run(operations, *, executor=None):
    service = ChatService(
        operations=operations,
        jobs=ChatJobs(),
        query_executor=executor or ErrorExecutor(PgError(None)),
    )
    return service, service.run("question", CONFIG, on_accepted=lambda _: None)


def test_chat_loading_model_enospc_keeps_specific_safe_message():
    _, snapshot = _run(LoadingFailureOperations(OSError(errno.ENOSPC, "No space left on device")))
    assert snapshot.state is ChatJobState.FAILED
    assert snapshot.error and snapshot.error.code == "MODEL_LOAD_ERROR"
    assert "espaço suficiente em disco" in snapshot.error.message
    assert snapshot.error.retryable is True


def test_chat_loading_model_cuda_oom_keeps_specific_safe_message():
    _, snapshot = _run(LoadingFailureOperations(RuntimeError("CUDA out of memory")))
    assert snapshot.error and snapshot.error.code == "MODEL_LOAD_ERROR"
    assert "memória suficiente na GPU" in snapshot.error.message


def test_chat_loading_model_sqlstate_connection_is_database_error():
    _, snapshot = _run(LoadingFailureOperations(PgError("08006")))
    assert snapshot.error and snapshot.error.code == "DATABASE_CONNECTION_ERROR"
    assert snapshot.error.retryable is True


def test_chat_loading_model_postgresql_message_is_database_error():
    error = RuntimeError("connection to server database.example failed")
    _, snapshot = _run(LoadingFailureOperations(error))
    assert snapshot.error and snapshot.error.code == "DATABASE_CONNECTION_ERROR"
    assert "baixar" not in snapshot.error.message.lower()


def test_chat_loading_model_hugging_face_network_evidence_is_model_load_error():
    error = RuntimeError(
        "huggingface_hub snapshot_download: Temporary failure in name resolution"
    )
    _, snapshot = _run(LoadingFailureOperations(error))
    assert snapshot.error and snapshot.error.code == "MODEL_LOAD_ERROR"
    assert "falha de rede" in snapshot.error.message


def test_chat_loading_model_generic_connection_uses_conservative_fallback():
    _, snapshot = _run(LoadingFailureOperations(ConnectionError("transport failed")))
    assert snapshot.error and snapshot.error.code == "INTERNAL_ERROR"
    assert "banco" not in snapshot.error.message.lower()
    assert "baixar" not in snapshot.error.message.lower()


def test_chat_generating_generic_failure_is_sql_generation_error():
    _, snapshot = _run(GeneratingFailureOperations())
    assert snapshot.error and snapshot.error.code == "SQL_GENERATION_ERROR"
    assert "secret" not in snapshot.error.message


@pytest.mark.parametrize(
    ("sqlstate", "code", "retryable"),
    [
        ("08006", "DATABASE_CONNECTION_ERROR", True),
        ("42601", "SQL_SYNTAX_ERROR", False),
        ("57014", "QUERY_TIMEOUT", True),
        (None, "QUERY_EXECUTION_ERROR", True),
    ],
)
def test_chat_executing_classifies_database_failures(sqlstate, code, retryable):
    _, snapshot = _run(SuccessfulOperations(), executor=ErrorExecutor(PgError(sqlstate)))
    assert snapshot.error and snapshot.error.code == code
    assert snapshot.error.retryable is retryable


def test_chat_resource_busy_creates_no_job():
    jobs = ChatJobs()

    class Busy:
        def run_chat(self, *_args, **_kwargs):
            raise OperationCoordinatorError(
                OperationErrorCode.RESOURCE_BUSY,
                "Outra operação pesada está em andamento.",
                "synthetic",
                active_operation=OperationType.BENCHMARK,
            )

    service = ChatService(operations=Busy(), jobs=jobs, query_executor=ErrorExecutor(PgError(None)))
    with pytest.raises(OperationCoordinatorError):
        service.run("question", CONFIG, on_accepted=lambda _: None)
    assert jobs.cleanup() == ()


def test_chat_api_resource_busy_is_immediate_and_retryable(tmp_path):
    container = api_container(tmp_path)

    class BusyExecutor:
        def submit(self, *_args, **_kwargs):
            raise OperationCoordinatorError(
                OperationErrorCode.RESOURCE_BUSY,
                "Outra operação pesada está em andamento.",
                "synthetic",
                active_operation=OperationType.BENCHMARK,
            )

        def shutdown(self):
            pass

    container.chat_executor = BusyExecutor()  # type: ignore[assignment]
    payload = {
        "question": "pergunta",
        "database": CONFIG.database,
        "library": CONFIG.library,
        "model_id": CONFIG.model_id,
        "context": CONFIG.context,
    }
    with TestClient(create_app(container=container)) as client:
        response = client.post("/api/v1/chat/jobs", json=payload)
    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "RESOURCE_BUSY",
        "message": "Outra operação pesada está em andamento.",
        "retryable": True,
    }


def test_chat_unexpected_validation_error_is_safe_internal_error(monkeypatch):
    monkeypatch.setattr(
        "interface.backend.chat.service.approve_read_only",
        lambda _sql: (_ for _ in ()).throw(RuntimeError("token=secret /srv/private")),
    )
    _, snapshot = _run(SuccessfulOperations())
    assert snapshot.error and snapshot.error.code == "INTERNAL_ERROR"
    assert "secret" not in snapshot.error.message and "/srv" not in snapshot.error.message


def _handler_app(exception_factory):
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/failure")
    def failure():
        exception_factory()

    return app


def test_runtime_key_error_is_unsupported_combination():
    app = _handler_app(lambda: (_ for _ in ()).throw(RuntimeKeyError("safe", "secret")))
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/failure")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_COMBINATION"


def test_runtime_load_error_is_not_unsupported_combination():
    def fail():
        _raise_wrapped(OSError(errno.ENOSPC, "No space left on device"))

    with TestClient(_handler_app(fail), raise_server_exceptions=False) as client:
        response = client.get("/failure")
    assert response.json()["error"]["code"] == "MODEL_LOAD_ERROR"
    assert "espaço suficiente em disco" in response.json()["error"]["message"]


def test_unexpected_api_error_returns_internal_and_logs_sanitized(caplog):
    def fail():
        raise RuntimeError("token=api-secret postgresql://alice:pw@db/base /srv/private")

    with caplog.at_level(logging.INFO, logger="interface.runtime"):
        with TestClient(_handler_app(fail), raise_server_exceptions=False) as client:
            response = client.get("/failure")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert all(value not in response.text for value in ("api-secret", "alice", "/srv"))
    assert all(value not in caplog.text for value in ("api-secret", "alice", "/srv/private"))
