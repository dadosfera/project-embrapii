from fastapi.testclient import TestClient

from interface.backend.api.app import create_app
from interface.backend.operations import OperationType
from interface.backend.tests.test_api_health import api_container


def test_status_reports_safe_free_and_busy_state(tmp_path):
    container = api_container(tmp_path)
    with TestClient(create_app(container=container)) as client:
        free = client.get("/api/v1/status").json()
        assert free["is_busy"] is False
        assert free["runtime_loaded"] is False

        lease = container.coordinator.try_acquire(OperationType.GENERATE)
        try:
            busy = client.get("/api/v1/status").json()
        finally:
            container.coordinator.release(lease)
    assert busy["is_busy"] is True
    assert busy["active_operation"] == "GENERATE"
    assert "token" not in str(busy).lower()
