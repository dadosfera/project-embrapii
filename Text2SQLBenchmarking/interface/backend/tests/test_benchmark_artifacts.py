from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
import os

from interface.backend.benchmark.artifacts import BenchmarkArtifactError, BenchmarkArtifactStore, BenchmarkIdentity
from interface.backend.benchmark.models import ArtifactState
from interface.backend.tests.adapter_support import configuration
from interface.backend.tests.conftest import EXECUTION_DATA, GENERATION_DATA


def _identity() -> BenchmarkIdentity:
    return BenchmarkIdentity.create(configuration(), 42)


def _write(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(data)
    types = {"id": "int64", "question": "string", "sql_ground_truth": "string", "sql_generated": "string", "tempo_geracao": "float64"}
    if "execucoes_iguais" in data:
        types.update({"tempo_execucao_ground_truth": "float64", "execucao_correta_ground_truth": "boolean", "tempo_execucao_generated": "float64", "execucao_correta_generated": "boolean", "erro_execucao_generated": "string", "execucoes_iguais": "boolean"})
    frame.astype(types).to_parquet(path, index=False)


def test_detects_missing_generation_generation_only_and_complete(tmp_path):
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    identity = _identity()
    paths = store.paths_for(identity)
    assert store.inspect(identity).state is ArtifactState.NOT_STARTED
    _write(paths.generation, GENERATION_DATA)
    assert store.inspect(identity).state is ArtifactState.GENERATION_ONLY
    _write(paths.execution, EXECUTION_DATA)
    assert store.inspect(identity).state is ArtifactState.COMPLETE


def test_raw_examples_has_independent_artifact_identity_and_starts_empty(tmp_path):
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    default = BenchmarkIdentity.create(configuration(), 42)
    examples = BenchmarkIdentity.create(configuration(context="examples"), 42)
    default_paths = store.paths_for(default)
    examples_paths = store.paths_for(examples)

    _write(default_paths.generation, GENERATION_DATA)

    assert default.legacy_token == "rawModel"
    assert examples.legacy_token == "rawModel_exemplos"
    assert default_paths.generation.name == "queries_geradas_rawModel_42.parquet"
    assert examples_paths.generation.name == (
        "queries_geradas_rawModel_exemplos_42.parquet"
    )
    assert examples_paths.execution.name == (
        "queries_geradas_rawModel_exemplos_42_executado.parquet"
    )
    assert store.inspect(examples).state is ArtifactState.NOT_STARTED
    assert not examples_paths.generation.parent.joinpath("history").exists()


def test_archiving_raw_examples_does_not_move_raw_default_artifacts(tmp_path):
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    default = BenchmarkIdentity.create(configuration(), 42)
    examples = BenchmarkIdentity.create(configuration(context="examples"), 42)
    default_paths = store.paths_for(default)
    examples_paths = store.paths_for(examples)
    _write(default_paths.generation, GENERATION_DATA)
    _write(examples_paths.generation, GENERATION_DATA)
    _write(examples_paths.execution, EXECUTION_DATA)

    archived = store.archive_existing(
        examples,
        now=lambda: datetime(2026, 7, 31, 10, 0, 0, tzinfo=timezone.utc),
    )

    archived_names = {
        path.name
        for path in (store.resources_root / archived.history_directory).iterdir()
    }
    assert default_paths.generation.exists()
    assert not examples_paths.generation.exists()
    assert not examples_paths.execution.exists()
    assert archived_names == {
        "queries_geradas_rawModel_exemplos_42.parquet",
        "queries_geradas_rawModel_exemplos_42_executado.parquet",
    }


def test_rejects_invalid_partial_and_execution_without_generation(tmp_path):
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    identity = _identity()
    paths = store.paths_for(identity)
    _write(paths.execution, EXECUTION_DATA)
    assert store.inspect(identity).state is ArtifactState.INVALID_RESULT
    paths.execution.unlink()
    partial = dict(EXECUTION_DATA)
    partial.pop("execucoes_iguais")
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, partial)
    assert store.inspect(identity).state is ArtifactState.INVALID_RESULT


def test_archive_preserves_names_and_uses_deterministic_suffix(tmp_path):
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    identity = _identity()
    paths = store.paths_for(identity)
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)
    now = lambda: datetime(2026, 7, 31, 10, 0, 0, tzinfo=timezone.utc)
    first = store.archive_existing(identity, now=now)
    assert first.history_directory.endswith("history/20260731_100000")
    assert not paths.generation.exists()
    assert (store.resources_root / first.generation.relative_path).exists()
    _write(paths.generation, GENERATION_DATA)
    second = store.archive_existing(identity, now=now)
    assert second.history_directory.endswith("history/20260731_100000_01")


def test_paths_are_confined_and_symbolic_links_are_rejected(tmp_path):
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    identity = _identity()
    paths = store.paths_for(identity)
    outside = tmp_path / "outside.parquet"
    outside.write_bytes(b"synthetic")
    paths.generation.parent.mkdir(parents=True, exist_ok=True)
    paths.generation.symlink_to(outside)
    with pytest.raises(BenchmarkArtifactError):
        store.inspect(identity)
    with pytest.raises(BenchmarkArtifactError):
        store.snapshot(outside)


def test_archive_preflight_fails_before_moving_when_destination_is_not_writable(tmp_path, monkeypatch):
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    identity = _identity()
    paths = store.paths_for(identity)
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)
    before = (paths.generation.read_bytes(), paths.execution.read_bytes())
    original_access = os.access
    monkeypatch.setattr(
        os,
        "access",
        lambda path, mode: False if path == paths.generation.parent else original_access(path, mode),
    )

    with pytest.raises(BenchmarkArtifactError):
        store.archive_existing(identity, now=lambda: datetime.now(timezone.utc))

    assert paths.generation.read_bytes() == before[0]
    assert paths.execution.read_bytes() == before[1]
    assert not (paths.generation.parent / "history").exists()


def test_archive_preflight_rejects_filesystem_without_space_before_moving(tmp_path, monkeypatch):
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    identity = _identity()
    paths = store.paths_for(identity)
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)
    before = (paths.generation.read_bytes(), paths.execution.read_bytes())
    monkeypatch.setattr(
        "interface.backend.benchmark.artifacts.shutil.disk_usage",
        lambda _path: SimpleNamespace(free=0),
    )

    with pytest.raises(BenchmarkArtifactError) as raised:
        store.archive_existing(identity, now=lambda: datetime.now(timezone.utc))

    assert raised.value.code == "ARCHIVE_ERROR"
    assert paths.generation.read_bytes() == before[0]
    assert paths.execution.read_bytes() == before[1]
    assert not (paths.generation.parent / "history").exists()


def test_archive_translates_history_creation_failure(tmp_path, monkeypatch):
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    identity = _identity()
    paths = store.paths_for(identity)
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)
    history_root = paths.generation.parent / "history"
    original_mkdir = Path.mkdir

    def mkdir(path, *args, **kwargs):
        if path == history_root:
            raise OSError("falha sintética em history")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", mkdir)
    with pytest.raises(BenchmarkArtifactError) as raised:
        store.archive_existing(identity, now=lambda: datetime.now(timezone.utc))

    assert raised.value.code == "ARCHIVE_ERROR"
    assert paths.generation.exists() and paths.execution.exists()


def test_archive_translates_timestamp_directory_creation_failure(tmp_path, monkeypatch):
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    identity = _identity()
    paths = store.paths_for(identity)
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)
    history_root = paths.generation.parent / "history"
    history_root.mkdir()
    original_mkdir = Path.mkdir

    def mkdir(path, *args, **kwargs):
        if path.parent == history_root:
            raise OSError("falha sintética no timestamp")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", mkdir)
    with pytest.raises(BenchmarkArtifactError) as raised:
        store.archive_existing(identity, now=lambda: datetime.now(timezone.utc))

    assert raised.value.code == "ARCHIVE_ERROR"
    assert paths.generation.exists() and paths.execution.exists()


def test_archive_rolls_back_first_move_when_second_move_fails(tmp_path, monkeypatch):
    store = BenchmarkArtifactStore(tmp_path / "resources" / "out")
    identity = _identity()
    paths = store.paths_for(identity)
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, EXECUTION_DATA)
    before = (paths.generation.read_bytes(), paths.execution.read_bytes())
    original_replace = os.replace
    forward_moves = 0

    def replace(source, target):
        nonlocal forward_moves
        if source in (paths.generation, paths.execution):
            forward_moves += 1
            if forward_moves == 2:
                raise OSError("falha sintética")
        return original_replace(source, target)

    monkeypatch.setattr(os, "replace", replace)
    with pytest.raises(BenchmarkArtifactError) as raised:
        store.archive_existing(identity, now=lambda: datetime.now(timezone.utc))

    assert raised.value.code == "ARCHIVE_ERROR"
    assert paths.generation.read_bytes() == before[0]
    assert paths.execution.read_bytes() == before[1]
