"""Single-worker admission for in-memory Chat jobs."""
from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Any

from interface.backend.operations import OperationCoordinatorError, OperationErrorCode, OperationType

from .models import ChatJobSnapshot
from .service import ChatService


@dataclass(frozen=True)
class ChatSubmission:
    snapshot: ChatJobSnapshot


class ChatExecutor:
    def __init__(self, service: ChatService) -> None:
        self._service = service
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def submit(self, question: str, configuration: Any) -> ChatSubmission:
        accepted = threading.Event()
        result: dict[str, object] = {}

        def on_accepted(snapshot: ChatJobSnapshot) -> None:
            result["snapshot"] = snapshot
            accepted.set()

        def worker() -> None:
            try:
                self._service.run(question, configuration, on_accepted=on_accepted)
            except BaseException as exc:
                if not accepted.is_set():
                    result["error"] = exc
                    accepted.set()
            finally:
                if not accepted.is_set():
                    result["error"] = RuntimeError("admissão de Chat não confirmada")
                    accepted.set()
                with self._lock:
                    if self._thread is threading.current_thread():
                        self._thread = None

        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise OperationCoordinatorError(
                    OperationErrorCode.RESOURCE_BUSY,
                    "Outra operação pesada está em andamento.",
                    "thread de Chat ainda ativa",
                    active_operation=OperationType.CHAT,
                )
            thread = threading.Thread(target=worker, name="interface-chat", daemon=False)
            self._thread = thread
            thread.start()

        accepted.wait()
        error = result.get("error")
        if error is not None:
            raise error  # type: ignore[misc]
        snapshot = result.get("snapshot")
        if not isinstance(snapshot, ChatJobSnapshot):
            raise RuntimeError("worker de Chat terminou sem snapshot ACCEPTED")
        return ChatSubmission(snapshot)

    def shutdown(self) -> None:
        with self._lock:
            thread = self._thread
        if thread is None or thread is threading.current_thread():
            return
        thread.join()
        with self._lock:
            if self._thread is thread and not thread.is_alive():
                self._thread = None
