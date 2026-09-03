from fastapi.testclient import TestClient

from interface.backend.api.app import create_app
from interface.backend.benchmark.models import ArtifactState, BenchmarkAction, BenchmarkJobSnapshot, BenchmarkJobState, FileSnapshot
from interface.backend.tests.test_api_benchmark import ControlledRunners, _payload
from interface.backend.tests.test_api_health import api_container


def test_startup_reconciles_and_shutdown_uses_exclusive_service(tmp_path):
    container = api_container(tmp_path)
    missing = FileSnapshot("sih_database/x.parquet", False, None, None, None)
    container.journal.create(BenchmarkJobSnapshot(
        job_id="pending", configuration=(("database", "sih_database"), ("library", "raw_model"), ("model_id", "Qwen/Qwen2.5-Coder-7B-Instruct"), ("context", "default")), seed=42,
        action=BenchmarkAction.RUN_MISSING_STAGES, state=BenchmarkJobState.ACCEPTED,
        artifact_state=ArtifactState.NOT_STARTED, created_at="2026-01-01T00:00:00+00:00", updated_at="2026-01-01T00:00:00+00:00", generation_before=missing, execution_before=missing,
    ))
    runners = ControlledRunners(container.artifacts, block=True)
    container.benchmark._generation_runner = runners.generation
    container.benchmark._execution_runner = runners.execution
    calls = []
    original = container.operations.shutdown
    def shutdown_after_worker():
        assert runners.done.is_set()
        assert container.benchmark_executor._thread is None
        calls.append("shutdown")
        return original()
    container.operations.shutdown = shutdown_after_worker  # type: ignore[method-assign]
    with TestClient(create_app(container=container)) as client:
        assert container.journal.get("pending").state is BenchmarkJobState.INTERRUPTED
        assert client.post("/api/v1/benchmark/jobs", json=_payload()).status_code == 202
        assert runners.started.wait(timeout=1)
        runners.finish.set()
        assert runners.done.wait(timeout=1)
    assert calls == ["shutdown"]
    container.operations.shutdown = original  # type: ignore[method-assign]
