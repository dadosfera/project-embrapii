from __future__ import annotations

import threading

import pytest

from interface.backend.operations.coordinator import (
    OperationCoordinator,
    OperationCoordinatorError,
    OperationErrorCode,
    OperationType,
)
from interface.backend.operations.service import ExclusiveOperationService


class FakeAdapter:
    workspace = object()

    def __init__(
        self,
        coordinator: OperationCoordinator,
        *,
        generation_error: Exception | None = None,
        started: threading.Event | None = None,
        finish: threading.Event | None = None,
    ) -> None:
        self.coordinator = coordinator
        self.generation_error = generation_error
        self.started = started
        self.finish = finish
        self.questions: list[str] = []
        self.observed_operations: list[OperationType | None] = []

    def load(self) -> None:
        pass

    def release(self) -> None:
        pass

    def generate(self, question: str) -> object:
        self.questions.append(question)
        self.observed_operations.append(self.coordinator.status().active_operation)
        if self.started is not None:
            self.started.set()
        if self.finish is not None:
            assert self.finish.wait(timeout=1)
        if self.generation_error is not None:
            raise self.generation_error
        return object()


class FakeModelManager:
    def __init__(self, adapter: FakeAdapter, coordinator: OperationCoordinator) -> None:
        self.adapter = adapter
        self.coordinator = coordinator
        self.calls: list[tuple[str, OperationType | None]] = []

    def get_or_load(self, key: object, *, hf_token: str | None) -> FakeAdapter:
        self.calls.append(("get_or_load", self.coordinator.status().active_operation))
        return self.adapter

    def mark_used(self) -> None:
        self.calls.append(("mark_used", self.coordinator.status().active_operation))

    def expire_if_idle(self) -> bool:
        self.calls.append(("expire", self.coordinator.status().active_operation))
        return True

    def shutdown(self) -> None:
        self.calls.append(("shutdown", self.coordinator.status().active_operation))


def _service(*, generation_error: Exception | None = None, started=None, finish=None):
    coordinator = OperationCoordinator()
    adapter = FakeAdapter(
        coordinator,
        generation_error=generation_error,
        started=started,
        finish=finish,
    )
    manager = FakeModelManager(adapter, coordinator)
    return ExclusiveOperationService(manager, coordinator), manager, adapter


def test_ensure_runtime_loaded_and_generate_are_entirely_under_exclusion():
    service, manager, adapter = _service()
    key = object()

    assert service.ensure_runtime_loaded(key, hf_token="synthetic-token") is None
    result = service.generate(key, hf_token="synthetic-token", question="synthetic question")

    assert result is not None
    assert manager.calls == [
        ("get_or_load", OperationType.LOAD_RUNTIME),
        ("get_or_load", OperationType.GENERATE),
        ("mark_used", OperationType.GENERATE),
    ]
    assert adapter.observed_operations == [OperationType.GENERATE]
    assert not service.coordinator.status().is_busy


def test_service_does_not_offer_a_public_adapter_escape_hatch():
    service, _, _ = _service()

    assert not hasattr(service, "get_or_load_runtime")
    assert not hasattr(service, "execute_with_runtime")
    assert not hasattr(service, "adapter")
    assert not hasattr(service, "manager")
    assert hasattr(service, "_execute_with_runtime")


def test_mark_used_happens_only_after_success_and_failure_releases_lock():
    service, manager, _ = _service(generation_error=ValueError("synthetic failure"))

    with pytest.raises(ValueError):
        service.generate(object(), hf_token="synthetic-token", question="synthetic question")

    assert [call[0] for call in manager.calls] == ["get_or_load"]
    assert not service.coordinator.status().is_busy
    assert service.expire_if_idle() is True
    assert manager.calls[-1] == ("expire", OperationType.EXPIRE_RUNTIME)


def test_expiration_and_shutdown_are_rejected_while_generation_is_active():
    started = threading.Event()
    finish = threading.Event()
    service, manager, _ = _service(started=started, finish=finish)
    result: list[object] = []

    def generate() -> None:
        result.append(
            service.generate(object(), hf_token="synthetic-token", question="synthetic question")
        )

    worker = threading.Thread(target=generate)
    worker.start()
    assert started.wait(timeout=1)

    with pytest.raises(OperationCoordinatorError) as expire_error:
        service.expire_if_idle()
    with pytest.raises(OperationCoordinatorError) as shutdown_error:
        service.shutdown()

    assert expire_error.value.code is OperationErrorCode.RESOURCE_BUSY
    assert shutdown_error.value.code is OperationErrorCode.RESOURCE_BUSY
    assert manager.calls == [("get_or_load", OperationType.GENERATE)]

    finish.set()
    worker.join(timeout=1)

    assert not worker.is_alive()
    assert result
    assert manager.calls[-1] == ("mark_used", OperationType.GENERATE)


def test_service_error_messages_do_not_expose_question_token_or_path():
    secret_question = "pergunta /private/path SELECT secret"
    secret_token = "token-secret"
    service, _, _ = _service()
    lease = service.coordinator.try_acquire(OperationType.BENCHMARK)

    try:
        with pytest.raises(OperationCoordinatorError) as raised:
            service.generate(
                object(),
                hf_token=secret_token,
                question=secret_question,
            )
    finally:
        service.coordinator.release(lease)

    assert raised.value.code is OperationErrorCode.RESOURCE_BUSY
    assert secret_question not in str(raised.value)
    assert secret_token not in str(raised.value)
