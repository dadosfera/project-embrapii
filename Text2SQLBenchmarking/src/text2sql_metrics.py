"""Implementação científica única das métricas adicionais de Text-to-SQL."""

from __future__ import annotations

import math
import re

from Levenshtein import distance as levenshtein_distance
import numpy as np
import pandas as pd
import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from src.metric_contract import ADDITIONAL_METRIC_COLUMNS


MetricResult = dict[str, float | None]


def dialect_for_sgbd(sgbd: str) -> str:
    """Traduz o SGBD já conhecido pelo executor para um dialect do sqlglot."""

    dialects = {
        "postgresql": "postgres",
        "sqlite": "sqlite",
    }
    try:
        return dialects[sgbd]
    except KeyError as exc:
        raise ValueError(f"SGBD sem dialect de métricas cadastrado: {sgbd!r}") from exc


def soft_execution_f1(df_pred: pd.DataFrame, df_gold: pd.DataFrame) -> float:
    """F1 sobre conjuntos de linhas, ignorando ordem e multiplicidade."""

    if df_pred.empty or df_gold.empty:
        return 1.0 if df_pred.empty and df_gold.empty else 0.0
    set_pred = set(df_pred.itertuples(index=False, name=None))
    set_gold = set(df_gold.itertuples(index=False, name=None))
    intersection = len(set_pred & set_gold)
    precision = intersection / len(set_pred) if set_pred else 0.0
    recall = intersection / len(set_gold) if set_gold else 0.0
    return (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0.0
    )


def statistical_summarization(
    df_pred: pd.DataFrame,
    df_gold: pd.DataFrame,
) -> float:
    """Compara mean/std das colunas numéricas com tolerância absoluta 1e-2."""

    numeric_pred = df_pred.select_dtypes(include=[np.number])
    numeric_gold = df_gold.select_dtypes(include=[np.number])
    if numeric_pred.shape[1] != numeric_gold.shape[1] or numeric_pred.empty:
        return 1.0 if numeric_pred.empty and numeric_gold.empty else 0.0
    stats_pred = numeric_pred.describe().loc[["mean", "std"]].fillna(0).values
    stats_gold = numeric_gold.describe().loc[["mean", "std"]].fillna(0).values
    return 1.0 if np.allclose(stats_pred, stats_gold, atol=1e-2) else 0.0


def similarity_scoring(df_pred: pd.DataFrame, df_gold: pd.DataFrame) -> float:
    """Jaccard sobre sets de células convertidas para string."""

    values_pred = set(df_pred.astype(str).values.ravel())
    values_gold = set(df_gold.astype(str).values.ravel())
    union = len(values_pred | values_gold)
    return len(values_pred & values_gold) / union if union > 0 else 0.0


def ves_score(t_gt: float, t_generated: float, success: bool) -> float:
    """Valid Efficiency Score condicionado à EX oficial persistida."""

    if not success or t_generated <= 0:
        return 0.0
    return float(np.clip(t_gt / t_generated, 0.0, 1.0))


def _extract_components(sql: str, dialect: str) -> dict[str, set[str]] | None:
    try:
        parsed = sqlglot.parse_one(sql, read=dialect)
    except SqlglotError:
        return None
    return {
        "cols": {column.name.lower() for column in parsed.find_all(exp.Column)},
        "tabs": {table.name.lower() for table in parsed.find_all(exp.Table)},
        "aggs": {
            aggregate.key.upper() for aggregate in parsed.find_all(exp.AggFunc)
        },
        "conds": {
            operator.key
            for operator in parsed.find_all(
                (exp.EQ, exp.GT, exp.LT, exp.Like, exp.In)
            )
        },
    }


def exact_match(sql_pred: str, sql_gold: str, *, dialect: str) -> float:
    """Identidade dos componentes extraídos da AST."""

    pred = _extract_components(sql_pred, dialect)
    gold = _extract_components(sql_gold, dialect)
    return 1.0 if pred == gold and pred is not None else 0.0


def component_match(sql_pred: str, sql_gold: str, *, dialect: str) -> float:
    """Média de Jaccard nas categorias de componentes aplicáveis."""

    pred = _extract_components(sql_pred, dialect)
    gold = _extract_components(sql_gold, dialect)
    if not pred or not gold:
        return 0.0
    scores = [
        len(pred[key] & gold[key]) / len(pred[key] | gold[key])
        for key in gold
        if pred[key] | gold[key]
    ]
    return sum(scores) / len(scores) if scores else 1.0


def structural_correctness(
    sql_pred: str,
    sql_gold: str,
    *,
    dialect: str,
) -> float:
    """Compara a AST após anonimizar tabelas e colunas."""

    def anonymize(sql: str) -> str | None:
        try:
            parsed = sqlglot.parse_one(sql, read=dialect)
        except SqlglotError:
            return None
        for column in parsed.find_all(exp.Column):
            column.replace(
                exp.Column(this=exp.Identifier(this="col", quoted=False))
            )
        for table in parsed.find_all(exp.Table):
            table.replace(exp.Table(this=exp.Identifier(this="tab", quoted=False)))
        return parsed.sql()

    pred = anonymize(sql_pred)
    gold = anonymize(sql_gold)
    return 1.0 if pred == gold and pred is not None else 0.0


def logical_form_accuracy(sql_pred: str, sql_gold: str) -> float:
    """Igualdade textual após lowercase e normalização de whitespace."""

    normalize = lambda sql: " ".join(sql.lower().split())
    return 1.0 if normalize(sql_pred) == normalize(sql_gold) else 0.0


def leco_score(sql_pred: str, sql_gold: str) -> float:
    """Similaridade Levenshtein normalizada no nível de string."""

    distance = levenshtein_distance(sql_pred, sql_gold)
    return 1.0 - distance / max(len(sql_pred), len(sql_gold), 1)


def skeleton_correctness(sql_pred: str, sql_gold: str) -> float:
    """Compara somente a sequência de keywords definida na referência."""

    def skeleton(sql: str) -> str:
        return " ".join(
            re.findall(
                r"\b(SELECT|FROM|WHERE|JOIN|GROUP|BY|ORDER|LIMIT|HAVING)\b",
                sql.upper(),
            )
        )

    return 1.0 if skeleton(sql_pred) == skeleton(sql_gold) else 0.0


def pcm_f1(sql_pred: str, sql_gold: str, *, dialect: str) -> float:
    """Média do F1 parcial das categorias de componentes da AST."""

    pred = _extract_components(sql_pred, dialect)
    gold = _extract_components(sql_gold, dialect)
    if not pred or not gold:
        return 0.0
    scores: list[float] = []
    for key in gold:
        if not pred[key] and not gold[key]:
            continue
        intersection = len(pred[key] & gold[key])
        precision = intersection / len(pred[key]) if pred[key] else 0.0
        recall = intersection / len(gold[key]) if gold[key] else 0.0
        scores.append(
            2 * precision * recall / (precision + recall)
            if precision + recall > 0
            else 0.0
        )
    return sum(scores) / len(scores) if scores else 0.0


def query_affinity_score(
    sql_pred: str,
    sql_gold: str,
    df_pred: pd.DataFrame,
    df_gold: pd.DataFrame,
) -> float:
    """Combina LeCo e Similarity com pesos fixos de 0.5."""

    string_score = leco_score(sql_pred, sql_gold)
    result_score = (
        similarity_scoring(df_pred, df_gold)
        if not df_gold.empty
        else (1.0 if df_pred.empty else 0.0)
    )
    return 0.5 * string_score + 0.5 * result_score


def unavailable_additional_metrics() -> MetricResult:
    """Representa a decisão metodológica para falha da Ground Truth."""

    return {column: None for column in ADDITIONAL_METRIC_COLUMNS}


def calculate_additional_metrics(
    *,
    sql_pred: str,
    sql_gold: str,
    df_pred: pd.DataFrame | None,
    df_gold: pd.DataFrame | None,
    t_gt: float,
    t_generated: float,
    ground_truth_succeeded: bool,
    generated_succeeded: bool,
    execution_equal: bool,
    dialect: str,
) -> MetricResult:
    """Calcula as 12 métricas sem executar SQL e sem recalcular EX."""

    if not ground_truth_succeeded:
        return unavailable_additional_metrics()
    if df_gold is None:
        raise TypeError("resultado da Ground Truth ausente após execução bem-sucedida")

    structural = {
        "exact_match": exact_match(sql_pred, sql_gold, dialect=dialect),
        "component_match": component_match(sql_pred, sql_gold, dialect=dialect),
        "structural_correctness": structural_correctness(
            sql_pred,
            sql_gold,
            dialect=dialect,
        ),
        "logical_form_accuracy": logical_form_accuracy(sql_pred, sql_gold),
        "leco": leco_score(sql_pred, sql_gold),
        "skeleton_correctness": skeleton_correctness(sql_pred, sql_gold),
        "pcm_f1": pcm_f1(sql_pred, sql_gold, dialect=dialect),
    }

    if generated_succeeded:
        if df_pred is None:
            raise TypeError("resultado gerado ausente após execução bem-sucedida")
        result_metrics = {
            "soft_f1": soft_execution_f1(df_pred, df_gold),
            "stats": statistical_summarization(df_pred, df_gold),
            "similarity": similarity_scoring(df_pred, df_gold),
            "ves": ves_score(t_gt, t_generated, execution_equal),
            "query_affinity_score": query_affinity_score(
                sql_pred,
                sql_gold,
                df_pred,
                df_gold,
            ),
        }
    else:
        result_metrics = {
            "soft_f1": 0.0,
            "stats": 0.0,
            "similarity": 0.0,
            "ves": 0.0,
            "query_affinity_score": 0.0,
        }

    metrics = {**result_metrics, **structural}
    if set(metrics) != set(ADDITIONAL_METRIC_COLUMNS):
        raise RuntimeError("contrato interno das métricas está incompleto")
    for key, value in metrics.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"métrica {key} não retornou valor numérico")
        if not math.isfinite(float(value)):
            raise ValueError(f"métrica {key} retornou valor não finito")
    return {key: float(value) for key, value in metrics.items()}

