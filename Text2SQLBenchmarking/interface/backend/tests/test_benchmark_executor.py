from __future__ import annotations

from datetime import datetime, timezone
import threading

import pytest

from interface.backend.api.benchmark_executor import BenchmarkExecutor
from interface.backend.benchmark.models import (
    ArtifactState,
    BenchmarkAction,
    BenchmarkJobSnapshot,
    BenchmarkJobState,
    FileSnapshot,
)
from interface.backend.operations import OperationCoordinatorError, OperationErrorCode, OperationType
from interface.backend.tests.adapter_support import configuration


class BlockingBenchmark:
    """Fake determinístico: confirma admissão e só então aguarda liberação."""

    def __init__(self) -> None:
        self.started, self.finish = threading.Event(), threading.Event()
        self.calls = 0

    def run(self, _configuration, *, seed, action, on_accepted):
        self.calls += 1
        missing = FileSnapshot("synthetic.parquet", False, None, None, None)
        snapshot = BenchmarkJobSnapshot(
            job_id=f"job-{seed}",
            configuration=(("database", "sih_database"), ("library", "raw_model"), ("model_id", "Qwen/Qwen2.5-Coder-7B-Instruct"), ("context", "default")),
            seed=seed,
            action=action,
            state=BenchmarkJobState.ACCEPTED,
            artifact_state=ArtifactState.NOT_STARTED,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
            generation_before=missing,
            execution_before=missing,
        )
        on_accepted(snapshot)
        self.started.set()
        assert self.finish.wait(timeout=2)
        return snapshot


def test_executor_keeps_one_non_daemon_thread_and_allows_next_after_completion():
    benchmark = BlockingBenchmark()
    executor = BenchmarkExecutor(benchmark)  # type: ignore[arg-type]
    first = executor.submit(configuration(), seed=42, action=BenchmarkAction.RUN_MISSING_STAGES)
    original = executor._thread
    assert first.snapshot.job_id == "job-42"
    assert original is not None and original.is_alive() and not original.daemon
    assert benchmark.started.wait(timeout=1)

    with pytest.raises(OperationCoordinatorError) as raised:
        executor.submit(configuration(), seed=43, action=BenchmarkAction.RUN_MISSING_STAGES)
    assert raised.value.code is OperationErrorCode.RESOURCE_BUSY
    assert raised.value.active_operation is OperationType.BENCHMARK
    assert executor._thread is original
    assert benchmark.calls == 1

    benchmark.finish.set()
    original.join(timeout=1)
    assert not original.is_alive()
    assert executor._thread is None

    benchmark.started.clear()
    benchmark.finish.clear()
    second = executor.submit(configuration(), seed=43, action=BenchmarkAction.RUN_MISSING_STAGES)
    assert second.snapshot.job_id == "job-43"
    assert executor._thread is not original
    benchmark.finish.set()
    executor.shutdown()
    assert executor._thread is None


def test_shutdown_waits_for_active_worker_and_is_idempotent():
    benchmark = BlockingBenchmark()
    executor = BenchmarkExecutor(benchmark)  # type: ignore[arg-type]
    executor.submit(configuration(), seed=42, action=BenchmarkAction.RUN_MISSING_STAGES)
    assert benchmark.started.wait(timeout=1)

    entered, returned = threading.Event(), threading.Event()

    def shutdown() -> None:
        entered.set()
        executor.shutdown()
        returned.set()

    waiter = threading.Thread(target=shutdown)
    waiter.start()
    assert entered.wait(timeout=1)
    assert not returned.is_set()
    benchmark.finish.set()
    assert returned.wait(timeout=1)
    waiter.join(timeout=1)
    executor.shutdown()
    assert executor._thread is None


def test_worker_without_accepted_callback_fails_the_handshake_instead_of_waiting():
    class SilentBenchmark:
        def run(self, *_args, **_kwargs):
            return None

    executor = BenchmarkExecutor(SilentBenchmark())  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="sem confirmar admissão"):
        executor.submit(configuration(), seed=42, action=BenchmarkAction.RUN_MISSING_STAGES)
    thread = executor._thread
    assert thread is not None
    thread.join(timeout=1)
    assert executor._thread is None
