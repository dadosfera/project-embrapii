from interface.backend.operations import OperationCoordinator, OperationCoordinatorError, OperationType

def test_chat_and_benchmark_share_same_global_lease():
    coordinator=OperationCoordinator(); lease=coordinator.try_acquire(OperationType.CHAT)
    try:
        try: coordinator.try_acquire(OperationType.BENCHMARK); assert False
        except OperationCoordinatorError: pass
    finally: coordinator.release(lease)
