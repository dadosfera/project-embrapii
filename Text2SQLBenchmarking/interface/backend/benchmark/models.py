"""Snapshots imutáveis e estados do job de Benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from interface.backend.domain.errors import PublicErrorCode, public_error

from .metrics import BenchmarkMetrics


class BenchmarkJobState(str, Enum):
    ACCEPTED = "accepted"
    ARCHIVING = "archiving"
    LOADING_MODEL = "loading_model"
    GENERATING = "generating"
    GENERATION_COMPLETED = "generation_completed"
    EXECUTING = "executing"
    CALCULATING_METRICS = "calculating_metrics"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class ArtifactState(str, Enum):
    NOT_STARTED = "not_started"
    GENERATION_ONLY = "generation_only"
    COMPLETE = "complete"
    INVALID_RESULT = "invalid_result"


class BenchmarkAction(str, Enum):
    RUN_MISSING_STAGES = "run_missing_stages"
    REEXECUTE = "reexecute"


# Alias compatível com imports e snapshots das fases anteriores. A enumeração
# central em ``domain.errors`` é a fonte de verdade da Fase 11.
BenchmarkErrorCode = PublicErrorCode


@dataclass(frozen=True)
class BenchmarkError:
    code: BenchmarkErrorCode
    message: str
    retryable: bool | None = None

    def __post_init__(self) -> None:
        if self.retryable is None:
            object.__setattr__(self, "retryable", public_error(self.code).retryable)

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "code": self.code.value,
            "message": self.message,
            "retryable": bool(self.retryable),
        }


@dataclass(frozen=True)
class FileSnapshot:
    """Metadados do arquivo, sem conteúdo nem caminho absoluto."""

    relative_path: str
    exists: bool
    size: int | None
    mtime_ns: int | None
    sha256: str | None

    def as_dict(self) -> dict[str, str | int | bool | None]:
        return {
            "relative_path": self.relative_path,
            "exists": self.exists,
            "size": self.size,
            "mtime_ns": self.mtime_ns,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class BenchmarkJobSnapshot:
    """Registro público, serializável e independente da página do navegador."""

    job_id: str
    configuration: tuple[tuple[str, str], ...]
    seed: int
    action: BenchmarkAction
    state: BenchmarkJobState
    artifact_state: ArtifactState
    created_at: str
    updated_at: str
    generation_before: FileSnapshot
    execution_before: FileSnapshot
    generation_after: FileSnapshot | None = None
    execution_after: FileSnapshot | None = None
    archived_generation: FileSnapshot | None = None
    archived_execution: FileSnapshot | None = None
    history_directory: str | None = None
    result: BenchmarkMetrics | None = None
    error: BenchmarkError | None = None

    def __post_init__(self) -> None:
        """Mantém a configuração interna canônica e realmente imutável."""

        object.__setattr__(self, "configuration", tuple(sorted(self.configuration)))

    @property
    def is_terminal(self) -> bool:
        return self.state in {
            BenchmarkJobState.COMPLETED,
            BenchmarkJobState.FAILED,
            BenchmarkJobState.INTERRUPTED,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "configuration": dict(self.configuration),
            "seed": self.seed,
            "action": self.action.value,
            "state": self.state.value,
            "stage": self.state.value,
            "artifact_state": self.artifact_state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "generation_before": self.generation_before.as_dict(),
            "execution_before": self.execution_before.as_dict(),
            "generation_after": (
                self.generation_after.as_dict() if self.generation_after else None
            ),
            "execution_after": (
                self.execution_after.as_dict() if self.execution_after else None
            ),
            "archived_generation": (
                self.archived_generation.as_dict() if self.archived_generation else None
            ),
            "archived_execution": (
                self.archived_execution.as_dict() if self.archived_execution else None
            ),
            "history_directory": self.history_directory,
            "metrics": self.result.metrics_as_dict() if self.result else None,
            "counts": self.result.counts.as_dict() if self.result else None,
            "times": self.result.times.as_dict() if self.result else None,
            "error": self.error.as_dict() if self.error else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkJobSnapshot":
        def file_snapshot(value: dict[str, Any] | None) -> FileSnapshot | None:
            if value is None:
                return None
            return FileSnapshot(**value)

        error_data = data.get("error")
        result = (
            BenchmarkMetrics.from_dict(
                {
                    "metrics": data["metrics"],
                    "counts": data["counts"],
                    "times": data["times"],
                }
            )
            if data.get("metrics") is not None
            and data.get("counts") is not None
            and data.get("times") is not None
            else None
        )
        return cls(
            job_id=data["job_id"],
            configuration=tuple(sorted(data["configuration"].items())),
            seed=data["seed"],
            action=BenchmarkAction(data["action"]),
            state=BenchmarkJobState(data["state"]),
            artifact_state=ArtifactState(data["artifact_state"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            generation_before=file_snapshot(data["generation_before"]),  # type: ignore[arg-type]
            execution_before=file_snapshot(data["execution_before"]),  # type: ignore[arg-type]
            generation_after=file_snapshot(data.get("generation_after")),
            execution_after=file_snapshot(data.get("execution_after")),
            archived_generation=file_snapshot(data.get("archived_generation")),
            archived_execution=file_snapshot(data.get("archived_execution")),
            history_directory=data.get("history_directory"),
            result=result,
            error=(
                BenchmarkError(
                    code=BenchmarkErrorCode(error_data["code"]),
                    message=error_data["message"],
                    retryable=error_data.get("retryable"),
                )
                if error_data
                else None
            ),
        )
