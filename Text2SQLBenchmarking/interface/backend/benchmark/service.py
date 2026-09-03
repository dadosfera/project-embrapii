"""Orquestração síncrona do Benchmark sobre journal e exclusão global."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
import subprocess
import sys
from typing import Callable
from uuid import uuid4

from interface.backend.domain.capabilities import ConfigurationSelection, resolve_registry_name
from interface.backend.domain.artifacts import ArtifactValidationError
from interface.backend.diagnostics import log_diagnostic_event, log_subprocess_failure
from interface.backend.domain.errors import (
    PublicErrorCode,
    PublicErrorPayload,
    classify_execution_subprocess_error,
    classify_generation_subprocess_error,
    iter_exception_chain,
    public_error,
)
from interface.backend.operations.coordinator import OperationCoordinator, OperationType
from interface.backend.storage.parquet_reader import read_parquet_artifact

from .artifacts import BenchmarkArtifactError, BenchmarkArtifactStore, BenchmarkIdentity
from .journal import BenchmarkJournal
from .metrics import BenchmarkMetrics, BenchmarkMetricsError, calculate_benchmark_metrics
from .models import (
    ArtifactState,
    BenchmarkAction,
    BenchmarkError,
    BenchmarkErrorCode,
    BenchmarkJobSnapshot,
    BenchmarkJobState,
)
from .reexecution import (
    IssuedReexecutionIntent,
    ReexecutionIntentError,
    ReexecutionIntentStore,
)


BenchmarkRunner = Callable[[BenchmarkIdentity], None]
Clock = Callable[[], datetime]
AcceptedObserver = Callable[[BenchmarkJobSnapshot], None]
RuntimeReleaser = Callable[[], None]


class BenchmarkServiceError(Exception):
    def __init__(
        self,
        code: BenchmarkErrorCode,
        public_message: str,
        internal_detail: str,
        retryable: bool | None = None,
    ) -> None:
        payload = public_error(code, public_message, retryable)
        super().__init__(payload.message)
        self.code = payload.code
        self.public_message = payload.message
        self.retryable = payload.retryable
        self.internal_detail = internal_detail


def _now() -> datetime:
    return datetime.now().astimezone()


def _legacy_runner(script_name: str, project_root: Path) -> BenchmarkRunner:
    """Factory tardia que conserva exatamente a interface dos scripts atuais."""

    def run(identity: BenchmarkIdentity) -> None:
        registry = resolve_registry_name(identity.configuration.model_id)
        if not registry.is_valid or registry.value is None:
            raise RuntimeError("modelo sem nome legado")
        subprocess.run(
            [
                sys.executable,
                script_name,
                "--db_name",
                identity.configuration.database,
                "--model_name",
                registry.value,
                "--biblioteca",
                identity.legacy_token,
                "--random_seed",
                str(identity.seed),
            ],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    return run


class BenchmarkService:
    """Executa etapas faltantes sob ``BENCHMARK`` e salva cada transição.

    Os runners de produção invocam os scripts batch existentes com os mesmos
    argumentos legados. Testes injetam runners sintéticos; este módulo não
    importa os geradores, nem abre banco ou modelo por conta própria.
    """

    def __init__(
        self,
        *,
        journal: BenchmarkJournal,
        artifacts: BenchmarkArtifactStore,
        coordinator: OperationCoordinator,
        generation_runner: BenchmarkRunner | None = None,
        execution_runner: BenchmarkRunner | None = None,
        runtime_releaser: RuntimeReleaser = lambda: None,
        reexecution_intents: ReexecutionIntentStore | None = None,
        clock: Clock = _now,
    ) -> None:
        self._journal = journal
        self._artifacts = artifacts
        self._coordinator = coordinator
        project_root = artifacts.resources_root.parent.parent
        self._generation_runner = generation_runner or _legacy_runner(
            "run_sql_generate.py", project_root
        )
        self._execution_runner = execution_runner or _legacy_runner(
            "run_sql_execution.py", project_root
        )
        self._runtime_releaser = runtime_releaser
        self._reexecution_intents = reexecution_intents or ReexecutionIntentStore()
        self._clock = clock

    def create_reexecution_intent(
        self,
        configuration: ConfigurationSelection,
        *,
        seed: int,
    ) -> IssuedReexecutionIntent:
        """Confirma um resultado completo sem adquirir a operação pesada."""

        identity = BenchmarkIdentity.create(configuration, seed)
        inspection = self._artifacts.inspect(identity)
        if inspection.state is ArtifactState.COMPLETE:
            try:
                self._calculate_result(identity)
            except BenchmarkServiceError as exc:
                raise ReexecutionIntentError(
                    BenchmarkErrorCode.REEXECUTION_CONFIRMATION_REQUIRED,
                    "A reexecução só pode ser confirmada para um resultado completo e válido.",
                    exc.internal_detail,
                ) from exc
        return self._reexecution_intents.issue(identity, inspection)

    def run(
        self,
        configuration: ConfigurationSelection,
        *,
        seed: int,
        action: BenchmarkAction = BenchmarkAction.RUN_MISSING_STAGES,
        confirmation_token: str | None = None,
        on_accepted: AcceptedObserver | None = None,
    ) -> BenchmarkJobSnapshot:
        """Cria o job somente após adquirir a exclusão não bloqueante."""

        identity = BenchmarkIdentity.create(configuration, seed)
        if not isinstance(action, BenchmarkAction):
            raise BenchmarkServiceError(
                BenchmarkErrorCode.INTERNAL_ERROR,
                "A ação solicitada não é válida.",
                "action incompatível",
            )
        return self._coordinator.execute(
            OperationType.BENCHMARK,
            lambda: self._run_exclusive(
                identity,
                action,
                confirmation_token=confirmation_token,
                on_accepted=on_accepted,
            ),
        )

    def get(self, job_id: str) -> BenchmarkJobSnapshot:
        return self._journal.get(job_id)

    def latest(self) -> BenchmarkJobSnapshot | None:
        return self._journal.latest()

    def active(self) -> BenchmarkJobSnapshot | None:
        return self._journal.active()

    def reconcile_incomplete_jobs(self) -> tuple[BenchmarkJobSnapshot, ...]:
        """Reconcilia somente evidências integrais, sem retomar nenhum runner."""

        reconciled: list[BenchmarkJobSnapshot] = []
        for snapshot in self._journal.nonterminal():
            try:
                identity = BenchmarkIdentity.create(
                    ConfigurationSelection(**dict(snapshot.configuration)), snapshot.seed
                )
                inspection = self._artifacts.inspect(identity)
                generation_matches = self._matches_evidence(
                    snapshot, inspection.generation, "generation"
                )
                execution_matches = self._matches_evidence(
                    snapshot, inspection.execution, "execution"
                )
                if (
                    inspection.state is ArtifactState.COMPLETE
                    and generation_matches
                    and execution_matches
                ):
                    try:
                        result = self._calculate_result(identity)
                    except BenchmarkServiceError:
                        reconciled.append(
                            self._interrupt(snapshot, ArtifactState.INVALID_RESULT)
                        )
                        continue
                    reconciled.append(
                        self._save(
                            snapshot,
                            state=BenchmarkJobState.COMPLETED,
                            artifact_state=ArtifactState.COMPLETE,
                            result=result,
                            error=None,
                        )
                    )
                elif (
                    inspection.state is ArtifactState.GENERATION_ONLY
                    and generation_matches
                    and execution_matches
                ):
                    reconciled.append(
                        self._save(
                            snapshot,
                            state=BenchmarkJobState.GENERATION_COMPLETED,
                            artifact_state=ArtifactState.GENERATION_ONLY,
                            error=None,
                        )
                    )
                else:
                    reconciled.append(self._interrupt(snapshot, inspection.state))
            except Exception:
                reconciled.append(self._interrupt(snapshot, snapshot.artifact_state))
        return tuple(reconciled)

    def _matches_evidence(self, snapshot: BenchmarkJobSnapshot, current, kind: str) -> bool:
        """Exige igualdade de ``FileSnapshot`` completa, nunca só nome ou data."""

        after = (
            snapshot.generation_after if kind == "generation" else snapshot.execution_after
        )
        before = (
            snapshot.generation_before if kind == "generation" else snapshot.execution_before
        )
        if after is not None and current == after:
            return True
        # Ausência de execução pode ser comprovada pelo snapshot anterior após
        # a geração; arquivos existentes só reutilizam evidência ``before``
        # enquanto o job ainda não poderia tê-los alterado.
        if not current.exists:
            return current == before
        return (
            snapshot.state in {BenchmarkJobState.ACCEPTED, BenchmarkJobState.LOADING_MODEL}
            and current == before
        )

    def _interrupt(
        self,
        snapshot: BenchmarkJobSnapshot,
        artifact_state: ArtifactState,
    ) -> BenchmarkJobSnapshot:
        return self._save(
            snapshot,
            state=BenchmarkJobState.INTERRUPTED,
            artifact_state=artifact_state,
            error=BenchmarkError(
                BenchmarkErrorCode.INTERNAL_ERROR,
                "O Benchmark foi interrompido e deve ser iniciado novamente.",
            ),
        )

    def _run_exclusive(
        self,
        identity: BenchmarkIdentity,
        action: BenchmarkAction,
        *,
        confirmation_token: str | None,
        on_accepted: AcceptedObserver | None = None,
    ) -> BenchmarkJobSnapshot:
        inspection = self._artifacts.inspect(identity)
        if action is BenchmarkAction.REEXECUTE:
            try:
                self._reexecution_intents.consume(
                    confirmation_token,
                    identity,
                    inspection,
                )
            except ReexecutionIntentError as exc:
                raise BenchmarkServiceError(
                    exc.code,
                    exc.public_message,
                    exc.internal_detail,
                ) from exc
        snapshot = self._new_snapshot(identity, action, inspection)
        self._journal.create(snapshot)
        runtime_released = False
        try:
            if on_accepted is not None:
                on_accepted(snapshot)
            if action is BenchmarkAction.REEXECUTE:
                snapshot = self._save(snapshot, state=BenchmarkJobState.ARCHIVING)
                # O lock BENCHMARK já está retido. Usamos o lifecycle do
                # ModelManager diretamente para não adquirir um segundo lease.
                self._runtime_releaser()
                runtime_released = True
                archive = self._artifacts.archive_existing(
                    identity,
                    now=self._clock,
                    expected_generation=inspection.generation,
                    expected_execution=inspection.execution,
                )
                snapshot = self._save(
                    snapshot,
                    history_directory=archive.history_directory,
                    generation_after=None,
                    execution_after=None,
                    archived_generation=archive.generation,
                    archived_execution=archive.execution,
                    artifact_state=ArtifactState.NOT_STARTED,
                )
                inspection = self._artifacts.inspect(identity)
            elif inspection.state is ArtifactState.INVALID_RESULT:
                raise BenchmarkServiceError(
                    BenchmarkErrorCode.INVALID_PARQUET,
                    "Os artefatos existentes do Benchmark são inválidos.",
                    inspection.invalid_reason or "artefato inválido",
                )

            if inspection.state is ArtifactState.NOT_STARTED:
                snapshot = self._save(snapshot, state=BenchmarkJobState.LOADING_MODEL)
                if not runtime_released:
                    self._runtime_releaser()
                    runtime_released = True
                snapshot = self._save(snapshot, state=BenchmarkJobState.GENERATING)
                self._generation_runner(identity)
                inspection = self._artifacts.inspect(identity)
                if inspection.state is not ArtifactState.GENERATION_ONLY:
                    raise BenchmarkServiceError(
                        BenchmarkErrorCode.INVALID_PARQUET,
                        "A geração do Benchmark não produziu um artefato válido.",
                        "runner de geração não produziu Parquet de geração válido",
                    )
                snapshot = self._save(
                    snapshot,
                    state=BenchmarkJobState.GENERATION_COMPLETED,
                    artifact_state=inspection.state,
                    generation_after=inspection.generation,
                    execution_after=inspection.execution,
                )

            if inspection.state is ArtifactState.GENERATION_ONLY:
                snapshot = self._save(
                    snapshot,
                    state=BenchmarkJobState.EXECUTING,
                    artifact_state=inspection.state,
                    generation_after=inspection.generation,
                    execution_after=inspection.execution,
                )
                self._execution_runner(identity)
                inspection = self._artifacts.inspect(identity)
                if inspection.state is not ArtifactState.COMPLETE:
                    raise BenchmarkServiceError(
                        BenchmarkErrorCode.INVALID_PARQUET,
                        "A execução do Benchmark não produziu um artefato válido.",
                        "runner de execução não produziu Parquet executado válido",
                    )
                snapshot = self._save(
                    snapshot,
                    artifact_state=inspection.state,
                    generation_after=inspection.generation,
                    execution_after=inspection.execution,
                )

            if inspection.state is ArtifactState.COMPLETE:
                snapshot = self._save(
                    snapshot,
                    state=BenchmarkJobState.CALCULATING_METRICS,
                    artifact_state=inspection.state,
                    generation_after=inspection.generation,
                    execution_after=inspection.execution,
                )
                try:
                    result = self._calculate_result(identity)
                except BenchmarkServiceError:
                    snapshot = self._save(
                        snapshot,
                        artifact_state=ArtifactState.INVALID_RESULT,
                    )
                    raise
                return self._save(
                    snapshot,
                    state=BenchmarkJobState.COMPLETED,
                    result=result,
                )
            raise BenchmarkServiceError(
                BenchmarkErrorCode.INTERNAL_ERROR,
                "O Benchmark não pôde concluir as etapas necessárias.",
                "estado de artefato não terminal",
            )
        except BenchmarkServiceError as exc:
            return self._save(
                snapshot,
                state=BenchmarkJobState.FAILED,
                error=BenchmarkError(exc.code, exc.public_message, exc.retryable),
            )
        except BenchmarkArtifactError as exc:
            if exc.code == "REEXECUTION_STATE_CHANGED":
                code = BenchmarkErrorCode.REEXECUTION_STATE_CHANGED
            elif exc.code == "ARCHIVE_ERROR":
                code = BenchmarkErrorCode.ARCHIVE_ERROR
            else:
                code = BenchmarkErrorCode.INTERNAL_ERROR
            payload = public_error(
                code,
                (
                    "Os artefatos do Benchmark mudaram. Confirme a reexecução novamente."
                    if code is BenchmarkErrorCode.REEXECUTION_STATE_CHANGED
                    else "Não foi possível arquivar os artefatos existentes com segurança."
                    if code is BenchmarkErrorCode.ARCHIVE_ERROR
                    else None
                ),
            )
            log_diagnostic_event(
                "benchmark.artifact_failure",
                exception=exc,
                stage=snapshot.state.value,
                error_code=payload.code.value,
                job_id=snapshot.job_id,
            )
            return self._save(
                snapshot,
                state=BenchmarkJobState.FAILED,
                error=BenchmarkError(payload.code, payload.message, payload.retryable),
            )
        except Exception as exc:
            payload = self._classify_unexpected_failure(snapshot.state, exc)
            subprocess_error = next(
                (
                    item
                    for item in iter_exception_chain(exc)
                    if hasattr(item, "returncode")
                    and any(hasattr(item, field) for field in ("stdout", "stderr", "output"))
                ),
                None,
            )
            if subprocess_error is not None:
                log_subprocess_failure(
                    "benchmark.subprocess.failed",
                    subprocess_error,
                    phase=snapshot.state.value,
                )
            else:
                log_diagnostic_event(
                    "benchmark.job.failed",
                    exception=exc,
                    stage=snapshot.state.value,
                    error_code=payload.code.value,
                    job_id=snapshot.job_id,
                )
            return self._save(
                snapshot,
                state=BenchmarkJobState.FAILED,
                error=BenchmarkError(payload.code, payload.message, payload.retryable),
            )

    @staticmethod
    def _classify_unexpected_failure(
        state: BenchmarkJobState,
        exception: BaseException,
    ) -> PublicErrorPayload:
        if state is BenchmarkJobState.GENERATING:
            return classify_generation_subprocess_error(exception)
        if state is BenchmarkJobState.EXECUTING:
            return classify_execution_subprocess_error(exception)
        return public_error(PublicErrorCode.INTERNAL_ERROR)

    def _calculate_result(self, identity: BenchmarkIdentity) -> BenchmarkMetrics:
        try:
            artifact = read_parquet_artifact(
                self._artifacts.paths_for(identity).execution
            )
            return calculate_benchmark_metrics(artifact)
        except (ArtifactValidationError, BenchmarkMetricsError) as exc:
            raise BenchmarkServiceError(
                BenchmarkErrorCode.INVALID_PARQUET,
                "O resultado executado do Benchmark é inválido.",
                f"agregação falhou: {type(exc).__name__}",
            ) from exc

    def _new_snapshot(self, identity: BenchmarkIdentity, action: BenchmarkAction, inspection) -> BenchmarkJobSnapshot:
        timestamp = self._timestamp()
        return BenchmarkJobSnapshot(
            job_id=str(uuid4()),
            configuration=(
                ("database", identity.configuration.database),
                ("library", identity.configuration.library),
                ("model_id", identity.configuration.model_id),
                ("context", identity.configuration.context),
            ),
            seed=identity.seed,
            action=action,
            state=BenchmarkJobState.ACCEPTED,
            artifact_state=inspection.state,
            created_at=timestamp,
            updated_at=timestamp,
            generation_before=inspection.generation,
            execution_before=inspection.execution,
        )

    def _save(self, snapshot: BenchmarkJobSnapshot, **changes) -> BenchmarkJobSnapshot:
        next_state = changes.get("state", snapshot.state)
        if next_state is not snapshot.state and next_state not in _ALLOWED_TRANSITIONS[snapshot.state]:
            raise RuntimeError("transição de Benchmark incompatível")
        updated = replace(snapshot, updated_at=self._timestamp(), **changes)
        self._journal.save(updated)
        return updated

    def _timestamp(self) -> str:
        return self._clock().isoformat()


_ALLOWED_TRANSITIONS = {
    BenchmarkJobState.ACCEPTED: {
        BenchmarkJobState.ARCHIVING,
        BenchmarkJobState.LOADING_MODEL,
        BenchmarkJobState.EXECUTING,
        BenchmarkJobState.CALCULATING_METRICS,
        BenchmarkJobState.GENERATION_COMPLETED,
        BenchmarkJobState.COMPLETED,
        BenchmarkJobState.FAILED,
        BenchmarkJobState.INTERRUPTED,
    },
    BenchmarkJobState.ARCHIVING: {
        BenchmarkJobState.LOADING_MODEL,
        BenchmarkJobState.GENERATION_COMPLETED,
        BenchmarkJobState.COMPLETED,
        BenchmarkJobState.FAILED,
        BenchmarkJobState.INTERRUPTED,
    },
    BenchmarkJobState.LOADING_MODEL: {
        BenchmarkJobState.GENERATING,
        BenchmarkJobState.GENERATION_COMPLETED,
        BenchmarkJobState.COMPLETED,
        BenchmarkJobState.FAILED,
        BenchmarkJobState.INTERRUPTED,
    },
    BenchmarkJobState.GENERATING: {
        BenchmarkJobState.GENERATION_COMPLETED,
        BenchmarkJobState.COMPLETED,
        BenchmarkJobState.FAILED,
        BenchmarkJobState.INTERRUPTED,
    },
    BenchmarkJobState.GENERATION_COMPLETED: {
        BenchmarkJobState.EXECUTING,
        BenchmarkJobState.COMPLETED,
        BenchmarkJobState.FAILED,
        BenchmarkJobState.INTERRUPTED,
    },
    BenchmarkJobState.EXECUTING: {
        BenchmarkJobState.CALCULATING_METRICS,
        BenchmarkJobState.GENERATION_COMPLETED,
        BenchmarkJobState.COMPLETED,
        BenchmarkJobState.FAILED,
        BenchmarkJobState.INTERRUPTED,
    },
    BenchmarkJobState.CALCULATING_METRICS: {
        BenchmarkJobState.COMPLETED,
        BenchmarkJobState.FAILED,
        BenchmarkJobState.INTERRUPTED,
    },
    BenchmarkJobState.COMPLETED: set(),
    BenchmarkJobState.FAILED: set(),
    BenchmarkJobState.INTERRUPTED: set(),
}
