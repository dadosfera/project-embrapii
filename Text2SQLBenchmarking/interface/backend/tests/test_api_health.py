from fastapi.testclient import TestClient

from interface.backend.api.app import create_app
from interface.backend.api.dependencies import ApiContainer
from interface.backend.benchmark import BenchmarkArtifactStore, BenchmarkJournal, BenchmarkService
from interface.backend.operations import ExclusiveOperationService, OperationCoordinator
from interface.backend.runtime import ModelManager
from interface.backend.api.benchmark_executor import BenchmarkExecutor


def api_container(tmp_path, *, generation_runner=lambda _: None, execution_runner=lambda _: None):
    coordinator = OperationCoordinator()
    manager = ModelManager()
    operations = ExclusiveOperationService(manager, coordinator)
    journal = BenchmarkJournal(tmp_path / "interface" / ".runtime" / "journal.sqlite3")
    artifacts = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    benchmark = BenchmarkService(
        journal=journal,
        artifacts=artifacts,
        coordinator=coordinator,
        generation_runner=generation_runner,
        execution_runner=execution_runner,
        runtime_releaser=manager.shutdown,
    )
    return ApiContainer(
        coordinator, manager, operations, journal, artifacts, benchmark, BenchmarkExecutor(benchmark)
    )


def test_health_is_safe_and_app_containers_are_isolated(tmp_path):
    first = api_container(tmp_path / "one")
    second = api_container(tmp_path / "two")
    assert first.coordinator is first.operations.coordinator
    assert first.coordinator is not second.coordinator

    with TestClient(create_app(container=first)) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "api_version": "v1", "journal_available": True}
    assert "path" not in response.text.lower()
