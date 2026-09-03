from __future__ import annotations

import math

import pandas as pd
import pytest

from src.metric_contract import ADDITIONAL_METRIC_COLUMNS
from src.text2sql_metrics import (
    calculate_additional_metrics,
    component_match,
    dialect_for_sgbd,
    exact_match,
    leco_score,
    logical_form_accuracy,
    pcm_f1,
    query_affinity_score,
    similarity_scoring,
    skeleton_correctness,
    soft_execution_f1,
    statistical_summarization,
    structural_correctness,
    ves_score,
)


def frame(values: list[object], column: str = "value") -> pd.DataFrame:
    return pd.DataFrame({column: values})


@pytest.mark.parametrize(
    ("pred", "gold", "expected"),
    [
        (frame([1, 2]), frame([1, 2]), 1.0),
        (frame([1, 2]), frame([2, 3]), 0.5),
        (frame([2, 1]), frame([1, 2]), 1.0),
        (frame([1, 1, 2]), frame([1, 2]), 1.0),
        (frame([]), frame([]), 1.0),
        (frame([]), frame([1]), 0.0),
    ],
)
def test_soft_f1_uses_sets_of_rows(pred, gold, expected):
    assert soft_execution_f1(pred, gold) == expected


def test_soft_f1_uses_complete_row_tuples():
    pred = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    gold = pd.DataFrame({"a": [2, 1], "b": ["y", "z"]})
    assert soft_execution_f1(pred, gold) == 0.5


@pytest.mark.parametrize(
    ("pred", "gold", "expected"),
    [
        (frame([1.0, 2.0]), frame([1.0, 2.0]), 1.0),
        (frame([1.0, 2.0]), pd.DataFrame({"a": [1.0], "b": [2.0]}), 0.0),
        (frame([1.0]), frame([1.0]), 1.0),
        (frame([1.0, math.nan, 3.0]), frame([1.0, math.nan, 3.0]), 1.0),
        (frame([1.0, 2.0]), frame([1.005, 2.005]), 1.0),
        (frame([1.0, 2.0]), frame([1.1, 2.1]), 0.0),
    ],
)
def test_stats_preserves_received_numeric_summary(pred, gold, expected):
    assert statistical_summarization(pred, gold) == expected


def test_stats_returns_one_when_both_have_no_numeric_columns():
    assert statistical_summarization(frame(["a"]), frame(["b"])) == 1.0


@pytest.mark.parametrize(
    ("pred", "gold", "expected"),
    [
        (frame([1, 2]), frame([1, 2]), 1.0),
        (frame([1, 2]), frame([2, 3]), 1 / 3),
        (frame([1, 1, 2]), frame([1, 2]), 1.0),
        (frame([]), frame([]), 0.0),
        (frame([1]), frame(["1"]), 1.0),
    ],
)
def test_similarity_is_jaccard_over_stringified_cells(pred, gold, expected):
    assert similarity_scoring(pred, gold) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("t_gt", "t_generated", "success", "expected"),
    [
        (1.0, 1.0, True, 1.0),
        (1.0, 2.0, True, 0.5),
        (2.0, 1.0, True, 1.0),
        (1.0, 1.0, False, 0.0),
        (1.0, 0.0, True, 0.0),
        (1.0, -1.0, True, 0.0),
    ],
)
def test_ves_uses_current_execution_success(t_gt, t_generated, success, expected):
    assert ves_score(t_gt, t_generated, success) == expected


def test_exact_match_compares_ast_component_sets_not_text():
    assert exact_match("SELECT a FROM t", "select a from t", dialect="postgres") == 1.0
    assert exact_match("SELECT b FROM t", "SELECT a FROM t", dialect="postgres") == 0.0
    assert exact_match("SELECT (", "SELECT a", dialect="postgres") == 0.0


def test_component_match_handles_total_partial_empty_and_ast_categories():
    assert component_match("SELECT a FROM t", "SELECT a FROM t", dialect="postgres") == 1.0
    assert component_match("SELECT b FROM t", "SELECT a FROM t", dialect="postgres") == 0.5
    assert component_match("SELECT 1", "SELECT 2", dialect="postgres") == 1.0
    assert component_match(
        "SELECT SUM(a) FROM t WHERE a > 1",
        "SELECT SUM(a) FROM t WHERE a > 2",
        dialect="postgres",
    ) == 1.0
    assert component_match("SELECT (", "SELECT a", dialect="postgres") == 0.0


def test_structural_correctness_anonymizes_names_but_not_structure():
    assert structural_correctness(
        "SELECT a FROM t WHERE a > 1",
        "SELECT b FROM u WHERE b > 1",
        dialect="postgres",
    ) == 1.0
    assert structural_correctness(
        "SELECT a FROM t",
        "SELECT a FROM t WHERE a > 1",
        dialect="postgres",
    ) == 0.0
    assert structural_correctness("SELECT (", "SELECT a", dialect="postgres") == 0.0


def test_logical_form_accuracy_normalizes_only_case_and_whitespace():
    assert logical_form_accuracy(" SELECT  A\nFROM T ", "select a from t") == 1.0
    assert logical_form_accuracy("SELECT a FROM t", "SELECT b FROM t") == 0.0
    assert logical_form_accuracy("", "") == 1.0


@pytest.mark.parametrize(
    ("pred", "gold", "expected"),
    [
        ("SELECT 1", "SELECT 1", 1.0),
        ("abc", "ab", 2 / 3),
        ("ab", "abc", 2 / 3),
        ("", "", 1.0),
        ("ação", "acão", 0.75),
    ],
)
def test_leco_is_normalized_levenshtein(pred, gold, expected):
    assert leco_score(pred, gold) == pytest.approx(expected)


def test_skeleton_correctness_uses_only_received_keyword_sequence():
    assert skeleton_correctness("SELECT a FROM t", "select b from u") == 1.0
    assert skeleton_correctness("SELECT a FROM t WHERE a=1", "SELECT a FROM t") == 0.0
    assert skeleton_correctness(
        "SELECT a FROM t WHERE a IN (SELECT b FROM u)",
        "SELECT x FROM y WHERE x IN (SELECT z FROM w)",
    ) == 1.0
    assert skeleton_correctness("SELECT DISTINCT a FROM t", "SELECT a FROM t") == 1.0


def test_pcm_f1_handles_perfect_partial_empty_and_parse_failure():
    assert pcm_f1("SELECT a FROM t", "SELECT a FROM t", dialect="postgres") == 1.0
    assert pcm_f1("SELECT b FROM t", "SELECT a FROM t", dialect="postgres") == 0.5
    assert pcm_f1("SELECT 1", "SELECT 2", dialect="postgres") == 0.0
    assert pcm_f1("SELECT (", "SELECT a", dialect="postgres") == 0.0


def test_qas_uses_fixed_equal_weights_and_received_empty_rule():
    pred = frame([1])
    gold = frame([2])
    assert query_affinity_score("SELECT 1", "SELECT 1", pred, gold) == 0.5
    assert query_affinity_score("", "", frame([]), frame([])) == 1.0
    assert query_affinity_score("a", "b", frame([1]), frame([])) == 0.0


def test_calculator_gt_failure_returns_twelve_nulls():
    result = calculate_additional_metrics(
        sql_pred="SELECT 1",
        sql_gold="SELECT 1",
        df_pred=None,
        df_gold=None,
        t_gt=1.0,
        t_generated=1.0,
        ground_truth_succeeded=False,
        generated_succeeded=False,
        execution_equal=False,
        dialect="postgres",
    )
    assert result == {column: None for column in ADDITIONAL_METRIC_COLUMNS}


def test_calculator_generated_failure_zeroes_only_result_metrics():
    result = calculate_additional_metrics(
        sql_pred="SELECT 1",
        sql_gold="SELECT 1",
        df_pred=None,
        df_gold=frame([1]),
        t_gt=1.0,
        t_generated=1.0,
        ground_truth_succeeded=True,
        generated_succeeded=False,
        execution_equal=False,
        dialect="postgres",
    )
    assert {
        key: result[key]
        for key in ("soft_f1", "stats", "similarity", "ves", "query_affinity_score")
    } == {
        "soft_f1": 0.0,
        "stats": 0.0,
        "similarity": 0.0,
        "ves": 0.0,
        "query_affinity_score": 0.0,
    }
    assert all(result[key] is not None for key in set(result) - {
        "soft_f1", "stats", "similarity", "ves", "query_affinity_score"
    })


def test_current_ex_true_implies_soft_f1_one_for_successful_results():
    gold = pd.DataFrame({"reference": [1, 2]})
    generated = pd.DataFrame({"generated": [1, 2]})

    result = calculate_additional_metrics(
        sql_pred="SELECT value FROM generated",
        sql_gold="SELECT value FROM reference",
        df_pred=generated,
        df_gold=gold,
        t_gt=1.0,
        t_generated=1.0,
        ground_truth_succeeded=True,
        generated_succeeded=True,
        execution_equal=True,
        dialect="postgres",
    )

    assert result["soft_f1"] == 1.0


def test_unexpected_calculator_error_is_not_converted_to_zero():
    with pytest.raises(TypeError):
        calculate_additional_metrics(
            sql_pred=None,  # type: ignore[arg-type]
            sql_gold="SELECT 1",
            df_pred=frame([1]),
            df_gold=frame([1]),
            t_gt=1.0,
            t_generated=1.0,
            ground_truth_succeeded=True,
            generated_succeeded=True,
            execution_equal=True,
            dialect="postgres",
        )


def test_dialect_is_centralized_for_supported_batch_databases():
    assert dialect_for_sgbd("postgresql") == "postgres"
    assert dialect_for_sgbd("sqlite") == "sqlite"
    with pytest.raises(ValueError):
        dialect_for_sgbd("unknown")
