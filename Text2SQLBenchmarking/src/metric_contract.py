"""Nomes canônicos das métricas persistidas e publicadas pelo projeto."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricContract:
    key: str
    code: str
    parquet_column: str | None


METRIC_CONTRACTS = (
    MetricContract("execution_accuracy", "EX", None),
    MetricContract("soft_f1", "Soft_F1", "soft_f1"),
    MetricContract("stats", "Stats", "stats"),
    MetricContract("similarity", "Similarity", "similarity"),
    MetricContract("ves", "VES", "ves"),
    MetricContract("exact_match", "EM", "exact_match"),
    MetricContract("component_match", "CM", "component_match"),
    MetricContract(
        "structural_correctness",
        "StCo",
        "structural_correctness",
    ),
    MetricContract(
        "logical_form_accuracy",
        "LFA",
        "logical_form_accuracy",
    ),
    MetricContract("leco", "LeCo", "leco"),
    MetricContract(
        "skeleton_correctness",
        "SkCo",
        "skeleton_correctness",
    ),
    MetricContract("pcm_f1", "PCMF1", "pcm_f1"),
    MetricContract(
        "query_affinity_score",
        "QAS",
        "query_affinity_score",
    ),
)

ADDITIONAL_METRIC_CONTRACTS = tuple(
    contract for contract in METRIC_CONTRACTS if contract.parquet_column is not None
)
ADDITIONAL_METRIC_COLUMNS = tuple(
    contract.parquet_column
    for contract in ADDITIONAL_METRIC_CONTRACTS
    if contract.parquet_column is not None
)

