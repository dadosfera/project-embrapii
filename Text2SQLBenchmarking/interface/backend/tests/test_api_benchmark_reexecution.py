from __future__ import annotations

from fastapi.testclient import TestClient

from interface.backend.api.app import create_app
from interface.backend.benchmark.artifacts import BenchmarkIdentity
from interface.backend.tests.adapter_support import configuration
from interface.backend.tests.conftest import EXECUTION_DATA, GENERATION_DATA
from interface.backend.tests.test_api_benchmark import ControlledRunners, _payload, _write
from interface.backend.tests.test_api_health import api_container


def _complete(container) -> None:
    paths = container.artifacts.paths_for(BenchmarkIdentity.create(configuration(), 42))
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)


def _intent(client: TestClient, **changes):
    payload = _payload()
    payload.pop("action")
    payload.update(changes)
    return client.post("/api/v1/benchmark/reexecution-intents", json=payload)


def test_intent_requires_complete_result_and_returns_short_lived_opaque_token(tmp_path):
    container = api_container(tmp_path)
    with TestClient(create_app(container=container)) as client:
        refused = _intent(client)
        assert refused.status_code == 409
        assert refused.json()["error"]["code"] == "REEXECUTION_CONFIRMATION_REQUIRED"

        _complete(container)
        accepted = _intent(client)

    assert accepted.status_code == 200
    body = accepted.json()
    assert body["confirmationToken"]
    assert body["expiresInSeconds"] > 0
    assert "sih_database" not in body["confirmationToken"]


def test_reexecution_job_requires_token_and_valid_token_is_single_use(tmp_path):
    container = api_container(tmp_path)
    runners = ControlledRunners(container.artifacts)
    container.benchmark._generation_runner = runners.generation
    container.benchmark._execution_runner = runners.execution
    _complete(container)

    with TestClient(create_app(container=container)) as client:
        missing = client.post(
            "/api/v1/benchmark/jobs",
            json=_payload(action="reexecute"),
        )
        assert missing.status_code == 409
        assert missing.json()["error"]["code"] == "REEXECUTION_CONFIRMATION_REQUIRED"
        assert container.journal.latest() is None

        token = _intent(client).json()["confirmationToken"]
        accepted = client.post(
            "/api/v1/benchmark/jobs",
            json=_payload(action="reexecute", confirmationToken=token),
        )
        assert accepted.status_code == 202
        container.benchmark_executor.shutdown()
        completed = client.get(accepted.json()["poll"]).json()["job"]
        assert completed["state"] == "completed"
        assert completed["metrics"]["execution_accuracy"]["value"] == 1.0

        reused = client.post(
            "/api/v1/benchmark/jobs",
            json=_payload(action="reexecute", confirmationToken=token),
        )

    assert reused.status_code == 409
    assert reused.json()["error"]["code"] == "REEXECUTION_CONFIRMATION_REQUIRED"


def test_reexecution_rejects_token_for_different_identity_or_changed_snapshot(tmp_path):
    container = api_container(tmp_path)
    _complete(container)
    with TestClient(create_app(container=container)) as client:
        token = _intent(client).json()["confirmationToken"]
        different_seed = client.post(
            "/api/v1/benchmark/jobs",
            json=_payload(seed=43, action="reexecute", confirmationToken=token),
        )
        assert different_seed.status_code == 409
        assert different_seed.json()["error"]["code"] == "REEXECUTION_STATE_CHANGED"

        token = _intent(client).json()["confirmationToken"]
        paths = container.artifacts.paths_for(BenchmarkIdentity.create(configuration(), 42))
        changed = {key: list(value) for key, value in EXECUTION_DATA.items()}
        changed["question"] = ["Pergunta alterada depois da confirmação"]
        _write(paths.execution, changed)
        changed_snapshot = client.post(
            "/api/v1/benchmark/jobs",
            json=_payload(action="reexecute", confirmation_token=token),
        )

    assert changed_snapshot.status_code == 409
    assert changed_snapshot.json()["error"]["code"] == "REEXECUTION_STATE_CHANGED"
    assert paths.generation.exists() and paths.execution.exists()
