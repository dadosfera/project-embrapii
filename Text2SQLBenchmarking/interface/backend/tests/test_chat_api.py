from fastapi.testclient import TestClient

from interface.backend.api.app import create_app
from interface.backend.chat.executor import ChatSubmission
from interface.backend.chat.models import ChatJobSnapshot, ChatJobState
from interface.backend.domain.capabilities import ConfigurationSelection
from interface.backend.tests.test_api_health import api_container


CONFIGURATION = ConfigurationSelection(
    "sih_database",
    "raw_model",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    "default",
)


def _payload(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {"question": "Quantos registros existem?", **CONFIGURATION.__dict__}
    payload.update(changes)
    return payload


def test_chat_rejects_invalid_request_and_unsupported_combination(tmp_path):
    with TestClient(create_app(container=api_container(tmp_path))) as client:
        empty = client.post("/api/v1/chat/jobs", json=_payload(question="  "))
        extra = client.post("/api/v1/chat/jobs", json=_payload(history=[]))
        unsupported = client.post(
            "/api/v1/chat/jobs",
            json=_payload(library="premsql_agent"),
        )

    assert empty.status_code == 422
    assert empty.json() == {
        "error": {
            "code": "INVALID_REQUEST",
            "message": "A pergunta informada não é válida.",
            "retryable": False,
        }
    }
    assert extra.status_code == 422
    assert extra.json()["error"]["code"] == "INVALID_REQUEST"
    assert unsupported.status_code == 400
    assert unsupported.json()["error"] == {
        "code": "UNSUPPORTED_COMBINATION",
        "message": (
            "PremSQLAgent não está disponível no Chat nesta versão. "
            "Use-o no modo Benchmark."
        ),
        "retryable": False,
    }


def test_chat_http_creation_and_polling_preserve_public_snapshot(tmp_path):
    container = api_container(tmp_path)
    accepted = ChatJobSnapshot.accepted(CONFIGURATION)
    succeeded = accepted.update(
        state=ChatJobState.SUCCEEDED,
        sql="SELECT 1",
        columns=("total",),
        rows=((1,),),
        row_count=1,
        displayed_row_count=1,
        truncated=False,
        generation_time_seconds=1.25,
        execution_time_seconds=0.5,
    )
    submissions: list[tuple[str, ConfigurationSelection]] = []
    lookups: list[str] = []

    class FakeChatExecutor:
        def submit(self, question, configuration):
            submissions.append((question, configuration))
            return ChatSubmission(accepted)

        def shutdown(self):
            pass

    class FakeChat:
        def get(self, job_id):
            lookups.append(job_id)
            return succeeded

    container.chat_executor = FakeChatExecutor()  # type: ignore[assignment]
    container.chat = FakeChat()  # type: ignore[assignment]

    with TestClient(create_app(container=container)) as client:
        created = client.post("/api/v1/chat/jobs", json=_payload())
        polled = client.get(f"/api/v1/chat/jobs/{accepted.job_id}")

    assert created.status_code == 202
    assert created.json()["job_id"] == accepted.job_id
    assert created.json()["state"] == "accepted"
    assert created.json()["poll"] == f"/api/v1/chat/jobs/{accepted.job_id}"
    assert submissions == [("Quantos registros existem?", CONFIGURATION)]
    assert lookups == [accepted.job_id]
    assert polled.status_code == 200
    assert polled.json()["job"] == succeeded.as_dict()
    assert polled.json()["job"]["configuration"] == CONFIGURATION.__dict__
    assert polled.json()["job"]["sql"] == "SELECT 1"
    assert polled.json()["job"]["rows"] == [[1]]


def test_unknown_chat_job_is_safe_404(tmp_path):
    with TestClient(create_app(container=api_container(tmp_path))) as client:
        response = client.get("/api/v1/chat/jobs/missing")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "JOB_NOT_FOUND",
            "message": "O job de Chat não foi encontrado.",
            "retryable": False,
        }
    }


def test_chat_accepts_raw_model_examples_without_history_field(tmp_path):
    container = api_container(tmp_path)
    accepted = ChatJobSnapshot.accepted(
        ConfigurationSelection(
            "sih_database",
            "raw_model",
            "Qwen/Qwen2.5-Coder-7B-Instruct",
            "examples",
        )
    )
    submissions = []

    class FakeChatExecutor:
        def submit(self, question, configuration):
            submissions.append((question, configuration))
            return ChatSubmission(accepted)

        def shutdown(self):
            pass

    container.chat_executor = FakeChatExecutor()  # type: ignore[assignment]

    with TestClient(create_app(container=container)) as client:
        response = client.post(
            "/api/v1/chat/jobs",
            json=_payload(context="examples"),
        )

    assert response.status_code == 202
    assert submissions == [("Quantos registros existem?", accepted.configuration)]
