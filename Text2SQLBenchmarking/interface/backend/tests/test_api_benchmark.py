from __future__ import annotations

import threading

import pandas as pd
from fastapi.testclient import TestClient

from interface.backend.api.app import create_app
from interface.backend.benchmark.artifacts import BenchmarkIdentity
from interface.backend.benchmark.models import BenchmarkJobState
from interface.backend.tests.conftest import EXECUTION_DATA, GENERATION_DATA
from interface.backend.tests.test_api_health import api_container


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    types = {"id": "int64", "question": "string", "sql_ground_truth": "string", "sql_generated": "string", "tempo_geracao": "float64"}
    if "execucoes_iguais" in data:
        types.update({"tempo_execucao_ground_truth": "float64", "execucao_correta_ground_truth": "boolean", "tempo_execucao_generated": "float64", "execucao_correta_generated": "boolean", "erro_execucao_generated": "string", "execucoes_iguais": "boolean"})
    pd.DataFrame(data).astype(types).to_parquet(path, index=False)


class ControlledRunners:
    def __init__(self, store, *, block=False, fail=False):
        self.store, self.block, self.fail = store, block, fail
        self.started, self.finish, self.done = threading.Event(), threading.Event(), threading.Event()
        self.calls: list[str] = []

    def generation(self, identity):
        self.calls.append("generation")
        self.started.set()
        if self.block:
            assert self.finish.wait(timeout=2)
        if self.fail:
            raise RuntimeError("/secret/path SELECT question")
        _write(self.store.paths_for(identity).generation, GENERATION_DATA)

    def execution(self, identity):
        self.calls.append("execution")
        _write(self.store.paths_for(identity).execution, EXECUTION_DATA)
        self.done.set()


def _payload(seed=42, **changes):
    value = {"database": "sih_database", "library": "raw_model", "model_id": "Qwen/Qwen2.5-Coder-7B-Instruct", "context": "default", "seed": seed, "action": "run_missing_stages"}
    value.update(changes)
    return value


def test_benchmark_returns_accepted_after_persistence_then_completes(tmp_path):
    container = api_container(tmp_path)
    runners = ControlledRunners(container.artifacts, block=True)
    container.benchmark._generation_runner = runners.generation
    container.benchmark._execution_runner = runners.execution
    with TestClient(create_app(container=container)) as client:
        response = client.post("/api/v1/benchmark/jobs", json=_payload())
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        assert response.json()["poll"] == f"/api/v1/benchmark/jobs/{job_id}"
        assert container.journal.get(job_id).state in {
            BenchmarkJobState.ACCEPTED,
            BenchmarkJobState.LOADING_MODEL,
            BenchmarkJobState.GENERATING,
        }
        assert runners.started.wait(timeout=1)
        runners.finish.set()
        assert runners.done.wait(timeout=1)
        container.benchmark_executor._thread.join(timeout=1)
        assert container.benchmark.get(job_id).state is BenchmarkJobState.COMPLETED
        assert client.get(f"/api/v1/benchmark/jobs/{job_id}").json()["job"]["state"] == "completed"


def test_busy_request_is_409_and_does_not_create_job(tmp_path):
    container = api_container(tmp_path)
    runners = ControlledRunners(container.artifacts, block=True)
    container.benchmark._generation_runner = runners.generation
    container.benchmark._execution_runner = runners.execution
    with TestClient(create_app(container=container)) as client:
        first = client.post("/api/v1/benchmark/jobs", json=_payload())
        assert first.status_code == 202 and runners.started.wait(timeout=1)
        second = client.post("/api/v1/benchmark/jobs", json=_payload(seed=43))
        assert second.status_code == 409
        assert second.json()["error"]["code"] == "RESOURCE_BUSY"
        assert container.journal.latest().job_id == first.json()["job_id"]
        runners.finish.set()
        assert runners.done.wait(timeout=1)
        container.benchmark_executor._thread.join(timeout=1)


def test_api_validation_lookup_and_safe_runner_failure(tmp_path):
    container = api_container(tmp_path)
    runners = ControlledRunners(container.artifacts, fail=True)
    container.benchmark._generation_runner = runners.generation
    container.benchmark._execution_runner = runners.execution
    with TestClient(create_app(container=container), raise_server_exceptions=False) as client:
        invalid = client.post("/api/v1/benchmark/jobs", json=_payload(action="invalid"))
        assert invalid.status_code == 422 and invalid.json()["error"]["code"] == "INVALID_REQUEST"
        incompatible = client.post("/api/v1/benchmark/jobs", json=_payload(library="xiyan_sql"))
        assert incompatible.status_code == 400
        unknown = client.get("/api/v1/benchmark/jobs/no-such-job")
        assert unknown.status_code == 404 and unknown.json()["error"]["code"] == "JOB_NOT_FOUND"
        accepted = client.post("/api/v1/benchmark/jobs", json=_payload())
        container.benchmark_executor._thread.join(timeout=1)
        job = container.benchmark.get(accepted.json()["job_id"])
    assert job.state is BenchmarkJobState.FAILED
    assert "/secret" not in job.error.message


def test_latest_and_active_are_nullable_without_jobs(tmp_path):
    with TestClient(create_app(container=api_container(tmp_path))) as client:
        assert client.get("/api/v1/benchmark/jobs/latest").json() == {"job": None}
        assert client.get("/api/v1/benchmark/jobs/active").json() == {"job": None}
