from __future__ import annotations

import pandas as pd
import pytest

import run_sql_execution
from src.executor import sqlExecutor
from src.metric_contract import ADDITIONAL_METRIC_COLUMNS


def generation_frame(sql_generated: str = "SELECT 1") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [1],
            "question": ["Pergunta sintética"],
            "sql_ground_truth": ["SELECT 1"],
            "sql_generated": [sql_generated],
            "tempo_geracao": [0.1],
        }
    )


class FakeExecutor:
    SGBD = "postgresql"

    def __init__(self, responses: list[pd.DataFrame | str]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, float]] = []
        self.comparisons = 0

    def execute_query(self, query, t=60):
        self.calls.append((str(query), t))
        return self.responses.pop(0)

    def _compare_dataframes(self, pred, gold):
        self.comparisons += 1
        return sqlExecutor._compare_dataframes(self, pred, gold)


def no_progress(items):
    return items


def test_pipeline_executes_each_sql_once_and_reuses_existing_dataframes():
    result_frame = pd.DataFrame({"value": [1]})
    executor = FakeExecutor([result_frame.copy(), result_frame.copy()])

    executed, _ = run_sql_execution.execute_queries(
        generation_frame(),
        executor,
        "datasus",
        progress=no_progress,
    )

    assert len(executor.calls) == 2
    assert executor.calls[0][0] == "SELECT 1"
    assert executor.calls[1][0] == "SELECT 1"
    assert executor.comparisons == 1
    assert bool(executed.loc[0, "execucoes_iguais"]) is True
    assert set(ADDITIONAL_METRIC_COLUMNS).issubset(executed.columns)
    assert executed.loc[0, list(ADDITIONAL_METRIC_COLUMNS)].notna().all()


def test_ground_truth_failure_preserves_ex_false_and_sets_all_metrics_null():
    executor = FakeExecutor(["erro GT", pd.DataFrame({"value": [1]})])

    executed, _ = run_sql_execution.execute_queries(
        generation_frame(),
        executor,
        "datasus",
        progress=no_progress,
    )

    assert len(executor.calls) == 2
    assert executor.comparisons == 0
    assert bool(executed.loc[0, "execucao_correta_ground_truth"]) is False
    assert bool(executed.loc[0, "execucoes_iguais"]) is False
    assert executed.loc[0, list(ADDITIONAL_METRIC_COLUMNS)].isna().all()


def test_generated_failure_zeroes_result_metrics_and_calculates_structural_metrics():
    executor = FakeExecutor([pd.DataFrame({"value": [1]}), "erro generated"])

    executed, _ = run_sql_execution.execute_queries(
        generation_frame(),
        executor,
        "datasus",
        progress=no_progress,
    )

    assert len(executor.calls) == 2
    assert executor.comparisons == 0
    assert bool(executed.loc[0, "execucao_correta_generated"]) is False
    assert bool(executed.loc[0, "execucoes_iguais"]) is False
    assert executed.loc[
        0,
        ["soft_f1", "stats", "similarity", "ves", "query_affinity_score"],
    ].tolist() == [0.0] * 5
    assert executed.loc[
        0,
        [
            "exact_match",
            "component_match",
            "structural_correctness",
            "logical_form_accuracy",
            "leco",
            "skeleton_correctness",
            "pcm_f1",
        ],
    ].notna().all()


def test_unexpected_metric_error_aborts_before_a_result_frame_exists(monkeypatch):
    source = generation_frame()
    executor = FakeExecutor(
        [pd.DataFrame({"value": [1]}), pd.DataFrame({"value": [1]})]
    )

    def fail(**_kwargs):
        raise TypeError("falha sintética")

    monkeypatch.setattr(run_sql_execution, "calculate_additional_metrics", fail)

    with pytest.raises(RuntimeError, match="metricas adicionais"):
        run_sql_execution.execute_queries(
            source,
            executor,
            "datasus",
            progress=no_progress,
        )

    assert len(executor.calls) == 2
    assert not set(ADDITIONAL_METRIC_COLUMNS).intersection(source.columns)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (pd.DataFrame({"a": [1, 2]}), pd.DataFrame({"x": [1, 2]}), True),
        (pd.DataFrame({"a": [2, 1]}), pd.DataFrame({"a": [1, 2]}), False),
        (pd.DataFrame({"a": [1]}), pd.DataFrame({"a": [1], "b": [2]}), False),
        (pd.DataFrame({"a": [1]}), pd.DataFrame({"a": [1.0]}), False),
        (pd.DataFrame({"a": [1]}), pd.DataFrame({"a": [2]}), False),
        (None, None, True),
        (None, pd.DataFrame(), False),
    ],
)
def test_execution_accuracy_comparison_regression(left, right, expected):
    executor = sqlExecutor()
    assert executor._compare_dataframes(left, right) is expected
