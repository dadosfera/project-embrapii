from __future__ import annotations

from datetime import datetime, timezone
import threading

import pandas as pd
import pytest

from interface.backend.benchmark.artifacts import BenchmarkArtifactError, BenchmarkArtifactStore, BenchmarkIdentity
from interface.backend.benchmark.journal import BenchmarkJournal
from interface.backend.benchmark.models import ArtifactState, BenchmarkAction, BenchmarkErrorCode, BenchmarkJobSnapshot, BenchmarkJobState
from interface.backend.benchmark.service import BenchmarkService, _legacy_runner
from interface.backend.benchmark.reexecution import ReexecutionIntentError
from interface.backend.operations.coordinator import OperationCoordinator, OperationCoordinatorError, OperationErrorCode
from interface.backend.runtime import ModelManager, RuntimeKey, RuntimeState
from interface.backend.adapters.workspace import RuntimeWorkspace
from interface.backend.domain.capabilities import ApplicationMode
from interface.backend.tests.adapter_support import configuration, create_project_root
from interface.backend.tests.conftest import EXECUTION_DATA, GENERATION_DATA


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(data)
    types = {"id": "int64", "question": "string", "sql_ground_truth": "string", "sql_generated": "string", "tempo_geracao": "float64"}
    if "execucoes_iguais" in data:
        types.update({"tempo_execucao_ground_truth": "float64", "execucao_correta_ground_truth": "boolean", "tempo_execucao_generated": "float64", "execucao_correta_generated": "boolean", "erro_execucao_generated": "string", "execucoes_iguais": "boolean"})
    frame.astype(types).to_parquet(path, index=False)


class Runners:
    def __init__(self, store, *, started=None, finish=None, error=None, execution_error=None):
        self.store, self.started, self.finish, self.error = store, started, finish, error
        self.execution_error = execution_error
        self.calls: list[str] = []

    def generation(self, identity):
        self.calls.append("generation")
        if self.started:
            self.started.set()
            assert self.finish.wait(timeout=1)
        if self.error:
            raise self.error
        path = self.store.paths_for(identity).generation
        _write(path, GENERATION_DATA)

    def execution(self, identity):
        self.calls.append("execution")
        if self.execution_error:
            raise self.execution_error
        path = self.store.paths_for(identity).execution
        _write(path, EXECUTION_DATA)


def _setup(tmp_path, *, store_class=BenchmarkArtifactStore, runners=None, runtime_releaser=lambda: None):
    store = store_class(tmp_path / "resources" / "out")
    journal = BenchmarkJournal(tmp_path / "interface" / ".runtime" / "journal.sqlite3")
    coordinator = OperationCoordinator()
    runners = runners or Runners(store)
    service = BenchmarkService(journal=journal, artifacts=store, coordinator=coordinator, generation_runner=runners.generation, execution_runner=runners.execution, runtime_releaser=runtime_releaser, clock=lambda: datetime(2026, 7, 31, 10, 0, 0, tzinfo=timezone.utc))
    return service, store, journal, runners, coordinator


def _confirmed_reexecution(service, *, seed=42):
    token = service.create_reexecution_intent(configuration(), seed=seed).token
    return service.run(
        configuration(),
        seed=seed,
        action=BenchmarkAction.REEXECUTE,
        confirmation_token=token,
    )


def test_runs_missing_stages_and_records_consistent_success(tmp_path):
    service, _, journal, runners, _ = _setup(tmp_path)
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.state is BenchmarkJobState.COMPLETED
    assert snapshot.artifact_state is ArtifactState.COMPLETE
    assert runners.calls == ["generation", "execution"]
    assert snapshot.result is not None
    assert snapshot.as_dict()["metrics"]["execution_accuracy"]["value"] == 1.0
    assert snapshot.as_dict()["counts"]["correct"] == 1
    assert snapshot.as_dict()["times"]["recorded_total"] == pytest.approx(0.28)
    assert journal.get(snapshot.job_id) == snapshot


def test_legacy_runner_uses_raw_examples_token_and_experiment_seed(tmp_path, monkeypatch):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))

    monkeypatch.setattr("interface.backend.benchmark.service.subprocess.run", run)
    identity = BenchmarkIdentity.create(
        configuration(context="examples"),
        43,
    )

    _legacy_runner("run_sql_generate.py", tmp_path)(identity)

    command, kwargs = calls[0]
    assert command[command.index("--biblioteca") + 1] == "rawModel_exemplos"
    assert command[command.index("--random_seed") + 1] == "43"
    assert kwargs["cwd"] == tmp_path
    assert kwargs["check"] is True


def test_reuses_generation_or_complete_artifacts_without_extra_runners(tmp_path):
    releases: list[str] = []
    service, store, _, runners, _ = _setup(
        tmp_path,
        runtime_releaser=lambda: releases.append("release"),
    )
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    _write(paths.generation, GENERATION_DATA)
    generation_before = paths.generation.read_bytes()
    assert service.run(configuration(), seed=42).state is BenchmarkJobState.COMPLETED
    assert runners.calls == ["execution"]
    assert releases == []
    assert paths.generation.read_bytes() == generation_before
    runners.calls.clear()
    assert service.run(configuration(), seed=42).state is BenchmarkJobState.COMPLETED
    assert runners.calls == []
    assert releases == []
    assert paths.generation.read_bytes() == generation_before


def test_invalid_artifact_fails_without_overwriting(tmp_path):
    service, store, _, runners, _ = _setup(tmp_path)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    paths.generation.parent.mkdir(parents=True, exist_ok=True)
    paths.generation.write_bytes(b"not parquet")
    before = paths.generation.read_bytes()
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.state is BenchmarkJobState.FAILED
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.INVALID_PARQUET
    assert runners.calls == []
    assert paths.generation.read_bytes() == before


def test_reexecution_archives_before_generating_and_never_overwrites_history(tmp_path):
    service, store, _, runners, _ = _setup(tmp_path)
    assert service.run(configuration(), seed=42).state is BenchmarkJobState.COMPLETED
    second = _confirmed_reexecution(service)
    assert second.history_directory and second.history_directory.endswith("20260731_100000")
    assert second.archived_generation and second.archived_execution
    archived_names = {path.name for path in (store.resources_root / second.history_directory).iterdir()}
    assert len(archived_names) == 2
    assert all(name.startswith("queries_geradas_rawModel_42") for name in archived_names)
    assert runners.calls == ["generation", "execution", "generation", "execution"]
    third = _confirmed_reexecution(service)
    assert third.history_directory and third.history_directory.endswith("20260731_100000_01")


def test_reexecution_without_complete_result_cannot_be_confirmed(tmp_path):
    service, store, _, runners, _ = _setup(tmp_path)

    with pytest.raises(ReexecutionIntentError):
        service.create_reexecution_intent(configuration(), seed=42)

    assert runners.calls == []
    assert not (store.paths_for(BenchmarkIdentity.create(configuration(), 42)).generation.parent / "history").exists()


def test_reexecution_with_generation_only_cannot_be_confirmed(tmp_path):
    service, store, _, runners, _ = _setup(tmp_path)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    _write(paths.generation, GENERATION_DATA)

    with pytest.raises(ReexecutionIntentError):
        service.create_reexecution_intent(configuration(), seed=42)

    assert paths.generation.exists()
    assert runners.calls == []


def test_reused_generation_persists_both_snapshots_before_execution_and_reconciles(tmp_path):
    service, store, journal, runners, coordinator = _setup(tmp_path)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    _write(paths.generation, GENERATION_DATA)
    runners.execution_error = SystemExit("simulate restart before execution")

    with pytest.raises(SystemExit):
        service.run(configuration(), seed=42)

    pending = journal.latest()
    assert pending and pending.state is BenchmarkJobState.EXECUTING
    assert pending.generation_after == store.snapshot(paths.generation)
    assert pending.execution_after == store.snapshot(paths.execution)
    assert pending.execution_after and not pending.execution_after.exists
    calls_before_reconcile = list(runners.calls)
    restarted = BenchmarkService(journal=BenchmarkJournal(tmp_path / "interface" / ".runtime" / "journal.sqlite3"), artifacts=store, coordinator=coordinator, generation_runner=runners.generation, execution_runner=runners.execution, clock=lambda: datetime(2026, 7, 31, 10, 0, 1, tzinfo=timezone.utc))
    assert restarted.reconcile_incomplete_jobs()[0].state is BenchmarkJobState.GENERATION_COMPLETED
    assert runners.calls == calls_before_reconcile


def test_reexecution_persists_new_generation_and_missing_execution_for_reconciliation(tmp_path):
    service, store, journal, runners, coordinator = _setup(tmp_path)
    assert service.run(configuration(), seed=42).state is BenchmarkJobState.COMPLETED
    runners.execution_error = SystemExit("simulate restart before execution")

    token = service.create_reexecution_intent(configuration(), seed=42).token
    with pytest.raises(SystemExit):
        service.run(configuration(), seed=42, action=BenchmarkAction.REEXECUTE, confirmation_token=token)

    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    pending = journal.latest()
    assert pending and pending.state is BenchmarkJobState.EXECUTING
    assert pending.history_directory and pending.archived_generation and pending.archived_execution
    assert pending.generation_after == store.snapshot(paths.generation)
    assert pending.execution_after == store.snapshot(paths.execution)
    assert pending.execution_after and not pending.execution_after.exists
    calls_before_reconcile = list(runners.calls)
    restarted = BenchmarkService(journal=BenchmarkJournal(tmp_path / "interface" / ".runtime" / "journal.sqlite3"), artifacts=store, coordinator=coordinator, generation_runner=runners.generation, execution_runner=runners.execution, clock=lambda: datetime(2026, 7, 31, 10, 0, 1, tzinfo=timezone.utc))
    assert restarted.reconcile_incomplete_jobs()[0].state is BenchmarkJobState.GENERATION_COMPLETED
    assert runners.calls == calls_before_reconcile


def test_new_execution_after_persisted_absence_remains_interrupted(tmp_path):
    service, store, journal, runners, _ = _setup(tmp_path)
    runners.execution_error = SystemExit("simulate restart before execution")

    with pytest.raises(SystemExit):
        service.run(configuration(), seed=42)

    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    _write(paths.execution, EXECUTION_DATA)
    assert service.reconcile_incomplete_jobs()[0].state is BenchmarkJobState.INTERRUPTED


def test_archive_failure_prevents_runners(tmp_path):
    class BrokenStore(BenchmarkArtifactStore):
        def archive_existing(self, identity, *, now, **_kwargs):
            raise BenchmarkArtifactError("ARCHIVE_ERROR", "synthetic")
    service, store, _, runners, _ = _setup(tmp_path, store_class=BrokenStore)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)
    token = service.create_reexecution_intent(configuration(), seed=42).token
    snapshot = service.run(configuration(), seed=42, action=BenchmarkAction.REEXECUTE, confirmation_token=token)
    assert snapshot.state is BenchmarkJobState.FAILED
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.ARCHIVE_ERROR
    assert runners.calls == []


def test_reexecution_rechecks_snapshots_immediately_before_archiving(tmp_path):
    service, store, _, runners, _ = _setup(tmp_path)
    assert service.run(configuration(), seed=42).state is BenchmarkJobState.COMPLETED
    token = service.create_reexecution_intent(configuration(), seed=42).token
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))

    def change_after_acceptance(_snapshot):
        changed = {key: list(value) for key, value in GENERATION_DATA.items()}
        changed["question"] = ["mudou depois da confirmação"]
        _write(paths.generation, changed)

    runners.calls.clear()
    snapshot = service.run(
        configuration(),
        seed=42,
        action=BenchmarkAction.REEXECUTE,
        confirmation_token=token,
        on_accepted=change_after_acceptance,
    )

    assert snapshot.state is BenchmarkJobState.FAILED
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.REEXECUTION_STATE_CHANGED
    assert paths.generation.exists() and paths.execution.exists()
    assert runners.calls == []


def test_runtime_release_failure_happens_before_archive_and_preserves_result(tmp_path):
    def fail_release():
        raise RuntimeError("falha sintética de release")

    service, store, _, runners, _ = _setup(tmp_path, runtime_releaser=fail_release)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)
    before = (paths.generation.read_bytes(), paths.execution.read_bytes())
    token = service.create_reexecution_intent(configuration(), seed=42).token

    snapshot = service.run(
        configuration(),
        seed=42,
        action=BenchmarkAction.REEXECUTE,
        confirmation_token=token,
    )

    assert snapshot.state is BenchmarkJobState.FAILED
    assert paths.generation.read_bytes() == before[0]
    assert paths.execution.read_bytes() == before[1]
    assert not (paths.generation.parent / "history").exists()
    assert runners.calls == []


def test_busy_does_not_create_partial_job_and_journal_is_readable_during_run(tmp_path):
    started, finish = threading.Event(), threading.Event()
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    runners = Runners(store, started=started, finish=finish)
    service, _, journal, _, _ = _setup(tmp_path, runners=runners)
    results = []
    worker = threading.Thread(target=lambda: results.append(service.run(configuration(), seed=42)))
    worker.start()
    assert started.wait(timeout=1)
    active = journal.latest()
    assert active and active.state is BenchmarkJobState.GENERATING
    with pytest.raises(OperationCoordinatorError) as raised:
        service.run(configuration(), seed=43)
    assert raised.value.code is OperationErrorCode.RESOURCE_BUSY
    assert journal.latest() == active
    finish.set()
    worker.join(timeout=1)
    assert not worker.is_alive()
    assert results and results[0].state is BenchmarkJobState.COMPLETED


def test_runner_failure_is_safe_and_releases_exclusion(tmp_path):
    service, _, _, runners, coordinator = _setup(tmp_path)
    runners.error = RuntimeError("secret /private/path SELECT")
    snapshot = service.run(configuration(), seed=42)
    assert snapshot.state is BenchmarkJobState.FAILED
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.SQL_GENERATION_ERROR
    assert "secret" not in snapshot.error.message
    assert "/private" not in snapshot.error.message
    assert not coordinator.status().is_busy


def test_execution_failure_is_safe_and_releases_exclusion(tmp_path):
    service, store, _, runners, coordinator = _setup(tmp_path)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    _write(paths.generation, GENERATION_DATA)
    runners.execution_error = RuntimeError("falha sintética")

    snapshot = service.run(configuration(), seed=42)

    assert snapshot.state is BenchmarkJobState.FAILED
    assert runners.calls == ["execution"]
    assert not coordinator.status().is_busy


def test_metrics_failure_marks_result_invalid_without_inventing_aggregates(tmp_path):
    service, store, _, runners, _ = _setup(tmp_path)

    def inconsistent_execution(identity):
        runners.calls.append("execution")
        data = {key: list(value) for key, value in EXECUTION_DATA.items()}
        data["execucao_correta_generated"] = [False]
        data["execucoes_iguais"] = [True]
        _write(store.paths_for(identity).execution, data)

    service._execution_runner = inconsistent_execution
    snapshot = service.run(configuration(), seed=42)

    assert snapshot.state is BenchmarkJobState.FAILED
    assert snapshot.artifact_state is ArtifactState.INVALID_RESULT
    assert snapshot.result is None
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.INVALID_PARQUET


def test_releases_retained_runtime_before_benchmark_generation(tmp_path):
    root = create_project_root(tmp_path / "project")
    events: list[str] = []

    class RetainedAdapter:
        def __init__(self, workspace):
            self.workspace = workspace

        def load(self):
            events.append("load_runtime")

        def release(self):
            events.append("release_runtime")

    manager = ModelManager(
        adapter_factory=lambda _key, workspace, _token: RetainedAdapter(workspace),
        workspace_factory=lambda: RuntimeWorkspace.create(project_root=root),
    )
    key = RuntimeKey.from_configuration(
        configuration(),
        ApplicationMode.CHAT,
        random_seed=42,
        hf_token="synthetic-token",
        project_root=root,
    )
    manager.get_or_load(key, hf_token="synthetic-token")
    service, _, _, runners, _ = _setup(
        tmp_path,
        runtime_releaser=manager.shutdown,
    )
    original_generation = service._generation_runner

    def generation(identity):
        events.append("generation_subprocess")
        original_generation(identity)

    service._generation_runner = generation

    snapshot = service.run(configuration(), seed=42)

    assert snapshot.state is BenchmarkJobState.COMPLETED
    assert events == ["load_runtime", "release_runtime", "generation_subprocess"]
    assert manager.state is RuntimeState.EMPTY


def test_accepted_callback_failure_marks_persisted_job_as_failed(tmp_path):
    service, _, journal, runners, _ = _setup(tmp_path)

    snapshot = service.run(
        configuration(),
        seed=42,
        on_accepted=lambda _: (_ for _ in ()).throw(RuntimeError("/secret/path")),
    )

    assert snapshot.state is BenchmarkJobState.FAILED
    assert journal.get(snapshot.job_id).state is BenchmarkJobState.FAILED
    assert snapshot.error and snapshot.error.code is BenchmarkErrorCode.INTERNAL_ERROR
    assert "/secret" not in snapshot.error.message
    assert runners.calls == []


def _pending_snapshot(job_id, state, generation_before, execution_before, *, generation_after=None, execution_after=None):
    return BenchmarkJobSnapshot(
        job_id=job_id,
        configuration=(("database", "sih_database"), ("library", "raw_model"), ("model_id", "Qwen/Qwen2.5-Coder-7B-Instruct"), ("context", "default")),
        seed=42,
        action=BenchmarkAction.RUN_MISSING_STAGES,
        state=state,
        artifact_state=ArtifactState.NOT_STARTED,
        created_at="2026-07-31T10:00:00+00:00",
        updated_at="2026-07-31T10:00:00+00:00",
        generation_before=generation_before,
        execution_before=execution_before,
        generation_after=generation_after,
        execution_after=execution_after,
    )


def test_reconcile_accepts_attributable_preexisting_complete_or_generation_only(tmp_path):
    service, store, journal, runners, _ = _setup(tmp_path)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)
    complete = _pending_snapshot("complete", BenchmarkJobState.ACCEPTED, store.snapshot(paths.generation), store.snapshot(paths.execution))
    journal.create(complete)
    assert service.reconcile_incomplete_jobs()[0].state is BenchmarkJobState.COMPLETED

    service, store, journal, runners, _ = _setup(tmp_path / "generation-only")
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    _write(paths.generation, GENERATION_DATA)
    generation_only = _pending_snapshot("generation", BenchmarkJobState.ACCEPTED, store.snapshot(paths.generation), store.snapshot(paths.execution))
    journal.create(generation_only)
    assert service.reconcile_incomplete_jobs()[0].state is BenchmarkJobState.GENERATION_COMPLETED
    assert runners.calls == []


@pytest.mark.parametrize("state", [BenchmarkJobState.GENERATION_COMPLETED, BenchmarkJobState.EXECUTING])
def test_reconcile_retains_attributable_generation_without_execution(tmp_path, state):
    service, store, journal, runners, _ = _setup(tmp_path)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    before_generation = store.snapshot(paths.generation)
    before_execution = store.snapshot(paths.execution)
    _write(paths.generation, GENERATION_DATA)
    journal.create(_pending_snapshot("generation-after", state, before_generation, before_execution, generation_after=store.snapshot(paths.generation)))
    assert service.reconcile_incomplete_jobs()[0].state is BenchmarkJobState.GENERATION_COMPLETED
    assert runners.calls == []


def test_reconcile_accepts_attributable_complete_after_calculating_metrics(tmp_path):
    service, store, journal, runners, _ = _setup(tmp_path)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    before_generation, before_execution = store.snapshot(paths.generation), store.snapshot(paths.execution)
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)
    journal.create(_pending_snapshot("after-complete", BenchmarkJobState.CALCULATING_METRICS, before_generation, before_execution, generation_after=store.snapshot(paths.generation), execution_after=store.snapshot(paths.execution)))
    result = service.reconcile_incomplete_jobs()[0]
    assert result.state is BenchmarkJobState.COMPLETED
    assert result.result is not None
    assert result.as_dict()["metrics"]["execution_accuracy"]["value"] == 1.0
    assert runners.calls == []


@pytest.mark.parametrize("state,with_execution", [(BenchmarkJobState.GENERATING, False), (BenchmarkJobState.EXECUTING, True)])
def test_reconcile_interrupts_unrecorded_new_artifacts(tmp_path, state, with_execution):
    service, store, journal, runners, _ = _setup(tmp_path)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    before_generation, before_execution = store.snapshot(paths.generation), store.snapshot(paths.execution)
    _write(paths.generation, GENERATION_DATA)
    if with_execution:
        _write(paths.execution, EXECUTION_DATA)
    journal.create(_pending_snapshot("unrecorded", state, before_generation, before_execution))
    result = service.reconcile_incomplete_jobs()[0]
    assert result.state is BenchmarkJobState.INTERRUPTED
    assert result.error and "iniciado novamente" in result.error.message
    assert runners.calls == []


@pytest.mark.parametrize("field", ["sha256", "size", "mtime_ns", "relative_path"])
def test_reconcile_interrupts_any_snapshot_divergence_or_invalid_result(tmp_path, field):
    service, store, journal, runners, _ = _setup(tmp_path)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)
    generation = store.snapshot(paths.generation)
    execution = store.snapshot(paths.execution)
    bad_value = "different" if field in {"sha256", "relative_path"} else 999999
    broken_generation = generation.__class__(**{**generation.as_dict(), field: bad_value})
    journal.create(_pending_snapshot("divergent", BenchmarkJobState.CALCULATING_METRICS, generation, execution, generation_after=broken_generation, execution_after=execution))
    assert service.reconcile_incomplete_jobs()[0].state is BenchmarkJobState.INTERRUPTED
    assert runners.calls == []


def test_reconcile_interrupts_invalid_result(tmp_path):
    service, store, journal, runners, _ = _setup(tmp_path)
    paths = store.paths_for(BenchmarkIdentity.create(configuration(), 42))
    paths.generation.parent.mkdir(parents=True, exist_ok=True)
    paths.generation.write_bytes(b"invalid")
    journal.create(_pending_snapshot("invalid", BenchmarkJobState.GENERATING, store.snapshot(paths.generation), store.snapshot(paths.execution)))
    assert service.reconcile_incomplete_jobs()[0].state is BenchmarkJobState.INTERRUPTED
    assert runners.calls == []


def test_restart_does_not_alter_terminal_jobs(tmp_path):
    service, store, journal, runners, _ = _setup(tmp_path)
    identity = BenchmarkIdentity.create(configuration(), 42)
    missing_generation = store.snapshot(store.paths_for(identity).generation)
    terminal = BenchmarkJobSnapshot(
        job_id="terminal-job",
        configuration=(("database", "sih_database"), ("library", "raw_model"), ("model_id", "Qwen/Qwen2.5-Coder-7B-Instruct"), ("context", "default")),
        seed=42,
        action=BenchmarkAction.RUN_MISSING_STAGES,
        state=BenchmarkJobState.COMPLETED,
        artifact_state=ArtifactState.NOT_STARTED,
        created_at="2026-07-31T10:00:00+00:00",
        updated_at="2026-07-31T10:00:00+00:00",
        generation_before=missing_generation,
        execution_before=store.snapshot(store.paths_for(identity).execution),
    )
    journal.create(terminal)
    assert service.reconcile_incomplete_jobs() == ()
    assert journal.get("terminal-job") == terminal
    assert runners.calls == []
