from __future__ import annotations

import json
from dataclasses import replace

import pytest

from interface.backend.benchmark.journal import BenchmarkJournal, BenchmarkJournalError
from interface.backend.benchmark.models import ArtifactState, BenchmarkAction, BenchmarkErrorCode, BenchmarkJobSnapshot, BenchmarkJobState, FileSnapshot


def _snapshot(
    job_id: str = "job-1",
    *,
    state: BenchmarkJobState = BenchmarkJobState.ACCEPTED,
    updated_at: str = "2026-07-31T10:00:00+00:00",
) -> BenchmarkJobSnapshot:
    artifact = FileSnapshot("sih_database/model/generated.parquet", False, None, None, None)
    return BenchmarkJobSnapshot(job_id=job_id, configuration=(("database", "sih_database"), ("library", "raw_model"), ("model_id", "Qwen/Qwen2.5-Coder-7B-Instruct"), ("context", "default")), seed=42, action=BenchmarkAction.RUN_MISSING_STAGES, state=state, artifact_state=ArtifactState.NOT_STARTED, created_at="2026-07-31T10:00:00+00:00", updated_at=updated_at, generation_before=artifact, execution_before=artifact)


def test_snapshot_is_immutable_serializable_and_safe(tmp_path):
    journal = BenchmarkJournal(tmp_path / "runtime" / "journal.sqlite3")
    snapshot = _snapshot()
    journal.create(snapshot)
    returned = journal.get(snapshot.job_id)
    assert returned == snapshot
    with pytest.raises(Exception):
        returned.seed = 99  # type: ignore[misc]
    payload = json.dumps(returned.as_dict())
    assert "token" not in payload
    assert "/home/" not in payload
    assert "SELECT" not in payload


def test_journal_known_unknown_and_persistent_reads(tmp_path):
    path = tmp_path / "runtime" / "journal.sqlite3"
    journal = BenchmarkJournal(path)
    snapshot = _snapshot()
    journal.create(snapshot)
    assert BenchmarkJournal(path).get(snapshot.job_id) == snapshot
    assert journal.latest() == snapshot
    assert journal.active() == snapshot
    assert journal.nonterminal() == (snapshot,)
    with pytest.raises(BenchmarkJournalError) as raised:
        journal.get("unknown")
    assert raised.value.code is BenchmarkErrorCode.JOB_NOT_FOUND

    completed = replace(snapshot, state=BenchmarkJobState.COMPLETED)
    journal.save(completed)
    assert journal.latest() == completed
    assert journal.active() is None
    assert journal.nonterminal() == ()


def test_nonterminal_and_active_are_ordered_by_updated_at_then_rowid(tmp_path):
    journal = BenchmarkJournal(tmp_path / "runtime" / "journal.sqlite3")
    first = _snapshot("first", updated_at="2026-07-31T10:00:00+00:00")
    second = _snapshot("second", state=BenchmarkJobState.GENERATING, updated_at="2026-07-31T10:00:00+00:00")
    journal.create(first)
    journal.create(second)
    updated_first = replace(first, updated_at="2026-07-31T10:01:00+00:00")
    journal.save(updated_first)

    assert tuple(item.job_id for item in journal.nonterminal()) == ("second", "first")
    assert journal.active() == updated_first
