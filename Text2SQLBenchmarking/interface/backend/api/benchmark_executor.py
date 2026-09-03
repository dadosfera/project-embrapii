"""Handshake curto para iniciar Benchmark em thread sem criar fila."""

from __future__ import annotations

from dataclasses import dataclass
import threading

from interface.backend.benchmark import BenchmarkAction, BenchmarkJobSnapshot, BenchmarkService
from interface.backend.domain.capabilities import ConfigurationSelection
from interface.backend.operations import (
    OperationCoordinatorError,
    OperationErrorCode,
    OperationType,
)


@dataclass(frozen=True)
class BenchmarkSubmission:
    snapshot: BenchmarkJobSnapshot


class BenchmarkExecutor:
    """Inicia no máximo um worker admitido pelo coordenador global.

    O ``Event`` serve apenas ao handshake de admissão da requisição HTTP; não
    armazena solicitações nem representa uma fila de jobs.
    """

    def __init__(self, benchmark: BenchmarkService) -> None:
        self._benchmark = benchmark
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def submit(
        self,
        configuration: ConfigurationSelection,
        *,
        seed: int,
        action: BenchmarkAction,
        confirmation_token: str | None = None,
    ) -> BenchmarkSubmission:
        accepted = threading.Event()
        result: dict[str, object] = {}

        def on_accepted(snapshot: BenchmarkJobSnapshot) -> None:
            result["snapshot"] = snapshot
            accepted.set()

        def worker() -> None:
            try:
                kwargs = {
                    "seed": seed,
                    "action": action,
                    "on_accepted": on_accepted,
                }
                if confirmation_token is not None:
                    kwargs["confirmation_token"] = confirmation_token
                self._benchmark.run(configuration, **kwargs)
            except BaseException as exc:
                if not accepted.is_set():
                    result["error"] = exc
                    accepted.set()
            finally:
                if not accepted.is_set():
                    result["error"] = RuntimeError(
                        "worker de Benchmark terminou sem confirmar admissão"
                    )
                    accepted.set()
                with self._lock:
                    if self._thread is threading.current_thread():
                        self._thread = None

        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise OperationCoordinatorError(
                    OperationErrorCode.RESOURCE_BUSY,
                    "Outra operação pesada está em andamento.",
                    "thread de Benchmark ainda ativa",
                    active_operation=OperationType.BENCHMARK,
                )
            # Uma thread já terminada não representa um job em fila.
            self._thread = None
            thread = threading.Thread(target=worker, name="interface-benchmark", daemon=False)
            self._thread = thread
            thread.start()

        accepted.wait()
        error = result.get("error")
        if error is not None:
            raise error  # type: ignore[misc]
        snapshot = result.get("snapshot")
        if not isinstance(snapshot, BenchmarkJobSnapshot):
            raise RuntimeError("worker de Benchmark não confirmou admissão")
        return BenchmarkSubmission(snapshot=snapshot)

    def shutdown(self) -> None:
        """Drena o Benchmark ativo sem cancelar escrita de artefatos ou journal."""

        with self._lock:
            thread = self._thread
        if thread is None or thread is threading.current_thread():
            return
        thread.join()
        with self._lock:
            if self._thread is thread and not thread.is_alive():
                self._thread = None
