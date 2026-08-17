from __future__ import annotations

import threading

import pytest

from interface.backend.operations.coordinator import (
    OperationCoordinator,
    OperationCoordinatorError,
    OperationErrorCode,
    OperationType,
)


def test_first_acquisition_is_accepted_and_release_clears_state():
    coordinator = OperationCoordinator()
    lease = coordinator.try_acquire(OperationType.GENERATE)

    assert coordinator.status().active_operation is OperationType.GENERATE
    coordinator.release(lease)

    assert coordinator.status().is_busy is False


def test_second_operation_is_rejected_immediately_without_calling_callback():
    coordinator = OperationCoordinator()
    lease = coordinator.try_acquire(OperationType.GENERATE)
    called = False

    try:
        with pytest.raises(OperationCoordinatorError) as raised:
            coordinator.execute(
                OperationType.EXPIRE_RUNTIME,
                lambda: called,
            )
    finally:
        coordinator.release(lease)

    assert raised.value.code is OperationErrorCode.RESOURCE_BUSY
    assert raised.value.active_operation is OperationType.GENERATE
    assert called is False


def test_execute_releases_after_success_and_exception():
    coordinator = OperationCoordinator()

    assert coordinator.execute(OperationType.LOAD_RUNTIME, lambda: "ok") == "ok"
    assert not coordinator.status().is_busy

    with pytest.raises(ValueError):
        coordinator.execute(OperationType.GENERATE, lambda: (_ for _ in ()).throw(ValueError()))

    assert not coordinator.status().is_busy
    assert coordinator.execute(OperationType.SHUTDOWN, lambda: "next") == "next"


def test_same_thread_reentrancy_is_rejected():
    coordinator = OperationCoordinator()

    def nested() -> None:
        coordinator.execute(OperationType.EXPIRE_RUNTIME, lambda: None)

    with pytest.raises(OperationCoordinatorError) as raised:
        coordinator.execute(OperationType.GENERATE, nested)

    assert raised.value.code is OperationErrorCode.RESOURCE_BUSY
    assert raised.value.active_operation is OperationType.GENERATE
    assert not coordinator.status().is_busy


def test_status_and_busy_error_expose_only_operation_type():
    coordinator = OperationCoordinator()
    lease = coordinator.try_acquire(OperationType.BENCHMARK)
    secret = "/private/question SELECT token"

    try:
        status = coordinator.status()
        with pytest.raises(OperationCoordinatorError) as raised:
            coordinator.execute(OperationType.SHUTDOWN, lambda: secret)
    finally:
        coordinator.release(lease)

    assert status.as_dict() == {
        "is_busy": True,
        "active_operation": "BENCHMARK",
    }
    assert secret not in str(raised.value)
    assert secret not in raised.value.internal_detail


def test_exactly_one_of_two_threads_enters_without_waiting_for_the_other():
    coordinator = OperationCoordinator()
    start = threading.Barrier(3)
    entered = threading.Event()
    finish = threading.Event()
    busy_returned = threading.Event()
    outcomes: list[str] = []

    def worker() -> None:
        start.wait()
        try:
            def operation() -> None:
                entered.set()
                assert finish.wait(timeout=1)

            coordinator.execute(OperationType.GENERATE, operation)
            outcomes.append("entered")
        except OperationCoordinatorError as exc:
            assert exc.code is OperationErrorCode.RESOURCE_BUSY
            outcomes.append("busy")
            busy_returned.set()

    first = threading.Thread(target=worker)
    second = threading.Thread(target=worker)
    first.start()
    second.start()
    start.wait()

    assert entered.wait(timeout=1)
    # A segunda thread já recebeu RESOURCE_BUSY; não há fila aguardando finish.
    assert busy_returned.wait(timeout=1)
    finish.set()
    first.join(timeout=1)
    second.join(timeout=1)

    assert not first.is_alive()
    assert not second.is_alive()
    assert sorted(outcomes) == ["busy", "entered"]
