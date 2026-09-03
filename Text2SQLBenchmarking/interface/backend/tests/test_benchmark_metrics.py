from __future__ import annotations

import pandas as pd
import pytest

from interface.backend.benchmark.metrics import (
    BenchmarkMetricsError,
    calculate_benchmark_metrics,
)
from interface.backend.storage.parquet_reader import read_parquet_artifact
from interface.backend.tests.conftest import EXECUTION_DATA
from src.metric_contract import ADDITIONAL_METRIC_COLUMNS
from src.metric_contract import ADDITIONAL_METRIC_CONTRACTS


def _artifact(tmp_path, rows: list[dict[str, object]]):
    data = {
        column: [row[column] for row in rows]
        for column in EXECUTION_DATA
    }
    frame = pd.DataFrame(data).astype(
        {
            "id": "int64",
            "question": "string",
            "sql_ground_truth": "string",
            "sql_generated": "string",
            "tempo_geracao": "float64",
            "tempo_execucao_ground_truth": "float64",
            "execucao_correta_ground_truth": "boolean",
            "tempo_execucao_generated": "float64",
            "execucao_correta_generated": "boolean",
            "erro_execucao_generated": "string",
            "execucoes_iguais": "boolean",
            **{column: "Float64" for column in ADDITIONAL_METRIC_COLUMNS},
        }
    )
    path = tmp_path / "executed.parquet"
    frame.to_parquet(path, index=False)
    return read_parquet_artifact(path)


def _row(**changes: object) -> dict[str, object]:
    row = {column: values[0] for column, values in EXECUTION_DATA.items()}
    row.update(changes)
    if changes.get("execucao_correta_ground_truth") is False:
        row.update({column: None for column in ADDITIONAL_METRIC_COLUMNS})
    return row


def test_calculates_execution_accuracy_partition_timeout_and_times(tmp_path):
    artifact = _artifact(
        tmp_path,
        [
            _row(tempo_geracao=1.0, tempo_execucao_ground_truth=2.0, tempo_execucao_generated=3.0),
            _row(id=2, execucoes_iguais=False, tempo_geracao=4.0, tempo_execucao_ground_truth=5.0, tempo_execucao_generated=6.0),
            _row(id=3, execucao_correta_generated=False, execucoes_iguais=False, erro_execucao_generated="Erro: A query excedeu o tempo limite de 30 segundos.", tempo_geracao=7.0, tempo_execucao_ground_truth=8.0, tempo_execucao_generated=9.0),
            _row(id=4, execucao_correta_ground_truth=False, execucoes_iguais=False, erro_execucao_generated="erro de banco sem timeout", tempo_geracao=10.0, tempo_execucao_ground_truth=11.0, tempo_execucao_generated=12.0),
        ],
    )

    result = calculate_benchmark_metrics(artifact)

    expected_metrics = {
        "execution_accuracy": {
            "value": 0.25,
            "available": True,
            "numerator": 1,
            "denominator": 4,
        }
    }
    expected_metrics.update(
        {
            contract.key: {
                "value": 1.0,
                "available": True,
                "denominator": 3,
            }
            for contract in ADDITIONAL_METRIC_CONTRACTS
        }
    )
    assert result.metrics_as_dict() == expected_metrics
    assert result.counts.as_dict() == {
        "total": 4,
        "correct": 1,
        "incorrect_without_error": 1,
        "errors": 2,
        "timeouts": 1,
    }
    assert (
        result.counts.correct
        + result.counts.incorrect_without_error
        + result.counts.errors
        == result.counts.total
    )
    assert result.times.as_dict() == {
        "generation": 22.0,
        "execution_ground_truth": 26.0,
        "execution_generated": 30.0,
        "execution_total": 56.0,
        "recorded_total": 78.0,
    }


def test_empty_executed_artifact_marks_execution_accuracy_unavailable(tmp_path):
    artifact = _artifact(tmp_path, [])

    result = calculate_benchmark_metrics(artifact)

    assert result.metrics_as_dict()["execution_accuracy"] == {
        "value": None,
        "available": False,
        "numerator": 0,
        "denominator": 0,
    }
    for metric in result.metrics[1:]:
        assert metric.as_dict() == {
            "value": None,
            "available": False,
            "denominator": 0,
        }
    assert result.counts.as_dict() == {
        "total": 0,
        "correct": 0,
        "incorrect_without_error": 0,
        "errors": 0,
        "timeouts": 0,
    }


def test_rejects_semantically_inconsistent_execution_flags(tmp_path):
    artifact = _artifact(
        tmp_path,
        [
            _row(
                execucao_correta_generated=False,
                execucoes_iguais=True,
                erro_execucao_generated="erro sintético",
            )
        ],
    )

    with pytest.raises(BenchmarkMetricsError):
        calculate_benchmark_metrics(artifact)


def test_additional_metric_aggregation_ignores_null_and_keeps_zero(tmp_path):
    artifact = _artifact(
        tmp_path,
        [
            _row(),
            _row(
                id=2,
                execucoes_iguais=False,
                **{column: 0.0 for column in ADDITIONAL_METRIC_COLUMNS},
            ),
            _row(
                id=3,
                execucao_correta_ground_truth=False,
                execucoes_iguais=False,
            ),
        ],
    )

    result = calculate_benchmark_metrics(artifact).metrics_as_dict()

    for contract in ADDITIONAL_METRIC_CONTRACTS:
        assert result[contract.key] == {
            "value": 0.5,
            "available": True,
            "denominator": 2,
        }


def test_additional_metric_aggregation_keeps_only_zero_as_available(tmp_path):
    artifact = _artifact(
        tmp_path,
        [
            _row(**{column: 0.0 for column in ADDITIONAL_METRIC_COLUMNS}),
        ],
    )

    result = calculate_benchmark_metrics(artifact).metrics_as_dict()

    for contract in ADDITIONAL_METRIC_CONTRACTS:
        assert result[contract.key] == {
            "value": 0.0,
            "available": True,
            "denominator": 1,
        }


def test_all_null_additional_metrics_are_unavailable(tmp_path):
    artifact = _artifact(
        tmp_path,
        [
            _row(
                execucao_correta_ground_truth=False,
                execucoes_iguais=False,
            ),
        ],
    )

    result = calculate_benchmark_metrics(artifact).metrics_as_dict()

    for contract in ADDITIONAL_METRIC_CONTRACTS:
        assert result[contract.key] == {
            "value": None,
            "available": False,
            "denominator": 0,
        }


def test_soft_f1_is_not_below_ex_when_both_use_total_denominator(tmp_path):
    artifact = _artifact(
        tmp_path,
        [
            _row(id=1, execucoes_iguais=True, soft_f1=1.0),
            _row(id=2, execucoes_iguais=False, soft_f1=0.5),
            _row(
                id=3,
                execucao_correta_generated=False,
                execucoes_iguais=False,
                erro_execucao_generated="erro sintético",
                soft_f1=0.0,
            ),
        ],
    )

    metrics = calculate_benchmark_metrics(artifact).metrics_as_dict()

    assert metrics["execution_accuracy"]["denominator"] == 3
    assert metrics["soft_f1"]["denominator"] == 3
    assert metrics["soft_f1"]["value"] >= metrics["execution_accuracy"]["value"]


def test_soft_f1_property_accounts_for_ground_truth_null_denominator(tmp_path):
    artifact = _artifact(
        tmp_path,
        [
            _row(id=1, execucoes_iguais=True, soft_f1=1.0),
            _row(
                id=2,
                execucao_correta_ground_truth=False,
                execucoes_iguais=False,
            ),
        ],
    )

    metrics = calculate_benchmark_metrics(artifact).metrics_as_dict()

    assert metrics["execution_accuracy"] == {
        "value": 0.5,
        "available": True,
        "denominator": 2,
        "numerator": 1,
    }
    assert metrics["soft_f1"] == {
        "value": 1.0,
        "available": True,
        "denominator": 1,
    }
