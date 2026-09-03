"""Container explícito de dependências com ciclo de vida por aplicação."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from fastapi import Request

from interface.backend.benchmark import BenchmarkArtifactStore, BenchmarkJournal, BenchmarkService
from interface.backend.operations import ExclusiveOperationService, OperationCoordinator
from interface.backend.runtime import ModelManager
from interface.backend.chat import ChatExecutor, ChatService
from interface.backend.chat.jobs import ChatJobs

from .benchmark_executor import BenchmarkExecutor


@dataclass
class ApiContainer:
    """Instâncias únicas usadas por uma aplicação FastAPI/processo."""

    coordinator: OperationCoordinator
    model_manager: ModelManager
    operations: ExclusiveOperationService
    journal: BenchmarkJournal
    artifacts: BenchmarkArtifactStore
    benchmark: BenchmarkService
    benchmark_executor: BenchmarkExecutor
    chat: ChatService | None = None
    chat_executor: ChatExecutor | None = None

    @classmethod
    def create(cls, *, project_root: Path | None = None) -> "ApiContainer":
        root = (project_root or Path(__file__).resolve().parents[3]).resolve()
        coordinator = OperationCoordinator()
        manager = ModelManager()
        operations = ExclusiveOperationService(manager, coordinator)
        runtime_root = root / "interface" / ".runtime"
        journal = BenchmarkJournal(runtime_root / "benchmark-journal.sqlite3")
        artifacts = BenchmarkArtifactStore(root / "resources" / "out")
        benchmark = BenchmarkService(
            journal=journal,
            artifacts=artifacts,
            coordinator=coordinator,
            runtime_releaser=manager.shutdown,
        )
        executor = BenchmarkExecutor(benchmark)
        chat_ttl = float(os.getenv("CHAT_RESULT_TTL_SECONDS", "900"))
        chat = ChatService(operations=operations, jobs=ChatJobs(ttl_seconds=chat_ttl))
        chat_executor = ChatExecutor(chat)
        return cls(coordinator, manager, operations, journal, artifacts, benchmark, executor, chat, chat_executor)


def get_container(request: Request) -> ApiContainer:
    return request.app.state.container
