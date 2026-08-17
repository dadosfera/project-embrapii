from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from interface.backend.domain.artifacts import (
    ArtifactKind,
    ArtifactValidationError,
    InvalidArtifactCode,
)
from interface.backend.storage.parquet_reader import read_parquet_artifact
from src.metric_contract import ADDITIONAL_METRIC_COLUMNS


@pytest.mark.parametrize(
    ("executed", "textual_id", "expected_kind", "expected_type"),
    [
        (False, False, ArtifactKind.GENERATION, "int64"),
        (False, True, ArtifactKind.GENERATION, "string"),
        (True, False, ArtifactKind.EXECUTED, "int64"),
        (True, True, ArtifactKind.EXECUTED, "string"),
    ],
)
def test_reads_generation_and_executed_with_supported_id_types(
    parquet_factory, executed, textual_id, expected_kind, expected_type
):
    path = parquet_factory(executed=executed, textual_id=textual_id)

    artifact = read_parquet_artifact(path)

    assert artifact.metadata.kind is expected_kind
    assert artifact.metadata.row_count == 1
    id_column = next(column for column in artifact.metadata.columns if column.name == "id")
    assert id_column.physical_type == expected_type


def test_accepts_empty_file_with_valid_schema(parquet_factory):
    artifact = read_parquet_artifact(parquet_factory(executed=True, empty=True))

    assert artifact.metadata.kind is ArtifactKind.EXECUTED
    assert artifact.metadata.row_count == 0
    assert artifact.dataframe.empty


def test_accepts_allowed_missing_error_message(parquet_factory):
    artifact = read_parquet_artifact(
        parquet_factory(
            executed=True,
            changes={
                "execucao_correta_generated": [False],
                "erro_execucao_generated": [None],
                "execucoes_iguais": [False],
            },
        )
    )

    error_column = next(
        column for column in artifact.metadata.columns
        if column.name == "erro_execucao_generated"
    )
    assert error_column.null_count == 1


def test_rejects_missing_required_column(parquet_factory):
    path = parquet_factory()
    frame = pd.read_parquet(path).drop(columns=["sql_generated"])
    frame.to_parquet(path, index=False)

    with pytest.raises(ArtifactValidationError) as raised:
        read_parquet_artifact(path)

    assert raised.value.code is InvalidArtifactCode.INVALID_PARQUET


def test_rejects_partial_execution_schema(parquet_factory):
    path = parquet_factory(executed=True)
    frame = pd.read_parquet(path).drop(columns=["execucoes_iguais"])
    frame.to_parquet(path, index=False)

    with pytest.raises(ArtifactValidationError):
        read_parquet_artifact(path)


def test_rejects_legacy_executed_schema_without_metric_columns(parquet_factory):
    path = parquet_factory(executed=True)
    frame = pd.read_parquet(path).drop(columns=list(ADDITIONAL_METRIC_COLUMNS))
    frame.to_parquet(path, index=False)

    with pytest.raises(ArtifactValidationError):
        read_parquet_artifact(path)


def test_rejects_missing_single_metric_column(parquet_factory):
    path = parquet_factory(executed=True)
    frame = pd.read_parquet(path).drop(columns=["component_match"])
    frame.to_parquet(path, index=False)

    with pytest.raises(ArtifactValidationError):
        read_parquet_artifact(path)


def test_rejects_null_in_required_column(parquet_factory):
    path = parquet_factory()
    frame = pd.read_parquet(path)
    frame.loc[0, "question"] = None
    frame.to_parquet(path, index=False)

    with pytest.raises(ArtifactValidationError):
        read_parquet_artifact(path)


def test_rejects_incompatible_type(parquet_factory):
    path = parquet_factory()
    frame = pd.read_parquet(path)
    frame["tempo_geracao"] = "não numérico"
    frame.to_parquet(path, index=False)

    with pytest.raises(ArtifactValidationError):
        read_parquet_artifact(path)


def test_rejects_incompatible_metric_type(parquet_factory):
    path = parquet_factory(executed=True)
    frame = pd.read_parquet(path)
    frame["soft_f1"] = "não numérico"
    frame.to_parquet(path, index=False)

    with pytest.raises(ArtifactValidationError):
        read_parquet_artifact(path)


@pytest.mark.parametrize("invalid_value", [float("nan"), float("inf")])
def test_rejects_non_finite_metric_values(parquet_factory, invalid_value):
    path = parquet_factory(executed=True)
    frame = pd.read_parquet(path)
    frame.loc[0, "soft_f1"] = invalid_value
    frame.to_parquet(path, index=False)

    with pytest.raises(ArtifactValidationError):
        read_parquet_artifact(path)


def test_metric_nullability_follows_ground_truth_execution(parquet_factory):
    path = parquet_factory(
        executed=True,
        changes={
            "execucao_correta_ground_truth": [False],
            "execucoes_iguais": [False],
            **{column: [None] for column in ADDITIONAL_METRIC_COLUMNS},
        },
    )
    artifact = read_parquet_artifact(path)
    assert artifact.dataframe.loc[0, list(ADDITIONAL_METRIC_COLUMNS)].isna().all()


def test_rejects_metric_null_when_ground_truth_succeeded(parquet_factory):
    path = parquet_factory(
        executed=True,
        changes={"component_match": [None]},
    )
    with pytest.raises(ArtifactValidationError):
        read_parquet_artifact(path)


def test_rejects_metric_value_when_ground_truth_failed(parquet_factory):
    path = parquet_factory(
        executed=True,
        changes={
            "execucao_correta_ground_truth": [False],
            "execucoes_iguais": [False],
        },
    )
    with pytest.raises(ArtifactValidationError):
        read_parquet_artifact(path)


@pytest.mark.parametrize("invalid_value", [float("nan"), float("inf")])
@pytest.mark.parametrize(
    ("column", "executed"),
    [
        ("tempo_geracao", False),
        ("tempo_execucao_ground_truth", True),
        ("tempo_execucao_generated", True),
    ],
)
def test_rejects_non_finite_time_values(
    parquet_factory, column, executed, invalid_value
):
    path = parquet_factory(executed=executed)
    frame = pd.read_parquet(path)
    frame.loc[0, column] = invalid_value
    frame.to_parquet(path, index=False)

    with pytest.raises(ArtifactValidationError):
        read_parquet_artifact(path)


def test_rejects_non_parquet_file(tmp_path: Path):
    path = tmp_path / "corrupted.parquet"
    path.write_bytes(b"isto nao e parquet")

    with pytest.raises(ArtifactValidationError):
        read_parquet_artifact(path)


def test_records_extra_columns_without_rejecting(parquet_factory):
    artifact = read_parquet_artifact(
        parquet_factory(extra_columns={"future_metadata": ["synthetic"]})
    )

    assert artifact.metadata.additional_columns == ("future_metadata",)
    assert "future_metadata" in artifact.dataframe.columns


def test_reading_does_not_modify_file(parquet_factory):
    path = parquet_factory(executed=True)
    before = (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)

    read_parquet_artifact(path)

    after = (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
    assert after == before


def test_public_error_does_not_expose_absolute_path(tmp_path: Path):
    path = tmp_path / "private" / "broken.parquet"

    with pytest.raises(ArtifactValidationError) as raised:
        read_parquet_artifact(path)

    assert str(path.resolve()) not in str(raised.value)
    assert str(raised.value) == ArtifactValidationError.public_message
