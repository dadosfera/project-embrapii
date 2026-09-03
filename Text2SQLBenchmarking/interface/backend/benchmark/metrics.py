"""Métricas agregadas e somente leitura para artefatos executados."""

from __future__ import annotations

from dataclasses import dataclass
import math

from interface.backend.domain.artifacts import ArtifactKind, ParquetArtifact, is_historical_timeout
from interface.backend.domain.metrics import METRIC_REGISTRY


class BenchmarkMetricsError(ValueError):
    """Indica dados executados que não admitem uma agregação confiável."""

    public_message = "O resultado executado tem dados semanticamente inconsistentes."


@dataclass(frozen=True)
class MetricValue:
    """Valor de uma métrica científica identificada por chave estável."""

    key: str
    value: float | None
    available: bool
    denominator: int
    numerator: int | None = None

    def as_dict(self) -> dict[str, float | int | bool | None]:
        result: dict[str, float | int | bool | None] = {
            "value": self.value,
            "available": self.available,
            "denominator": self.denominator,
        }
        if self.numerator is not None:
            result["numerator"] = self.numerator
        return result

    @classmethod
    def from_dict(
        cls, key: str, data: dict[str, float | int | bool | None]
    ) -> "MetricValue":
        return cls(
            key=key,
            value=float(data["value"]) if data["value"] is not None else None,
            available=bool(data["available"]),
            denominator=int(data["denominator"]),
            numerator=(
                int(data["numerator"])
                if data.get("numerator") is not None
                else None
            ),
        )


@dataclass(frozen=True)
class OperationalCounts:
    total: int
    correct: int
    incorrect_without_error: int
    errors: int
    timeouts: int

    def as_dict(self) -> dict[str, int]:
        return {
            "total": self.total,
            "correct": self.correct,
            "incorrect_without_error": self.incorrect_without_error,
            "errors": self.errors,
            "timeouts": self.timeouts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "OperationalCounts":
        return cls(**data)


@dataclass(frozen=True)
class RecordedTimes:
    generation: float
    execution_ground_truth: float
    execution_generated: float
    execution_total: float
    recorded_total: float

    def as_dict(self) -> dict[str, float]:
        return {
            "generation": self.generation,
            "execution_ground_truth": self.execution_ground_truth,
            "execution_generated": self.execution_generated,
            "execution_total": self.execution_total,
            "recorded_total": self.recorded_total,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "RecordedTimes":
        return cls(**data)


@dataclass(frozen=True)
class BenchmarkMetrics:
    """Resultado imutável, serializado em coleções extensíveis pela API."""

    metrics: tuple[MetricValue, ...]
    counts: OperationalCounts
    times: RecordedTimes

    def metrics_as_dict(self) -> dict[str, dict[str, float | int | bool | None]]:
        return {metric.key: metric.as_dict() for metric in self.metrics}

    def as_dict(self) -> dict[str, object]:
        return {
            "metrics": self.metrics_as_dict(),
            "counts": self.counts.as_dict(),
            "times": self.times.as_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "BenchmarkMetrics":
        metrics = data["metrics"]
        counts = data["counts"]
        times = data["times"]
        if not isinstance(metrics, dict) or not isinstance(counts, dict) or not isinstance(times, dict):
            raise ValueError("resultado agregado incompatível")
        registry_keys = [definition.key for definition in METRIC_REGISTRY]
        metric_keys = [key for key in registry_keys if key in metrics]
        metric_keys.extend(key for key in metrics if key not in registry_keys)
        return cls(
            metrics=tuple(
                MetricValue.from_dict(key, metrics[key])
                for key in metric_keys
                if isinstance(key, str) and isinstance(metrics[key], dict)
            ),
            counts=OperationalCounts.from_dict(counts),  # type: ignore[arg-type]
            times=RecordedTimes.from_dict(times),  # type: ignore[arg-type]
        )


def calculate_benchmark_metrics(artifact: ParquetArtifact) -> BenchmarkMetrics:
    """Calcula agregados sem modificar o DataFrame ou o Parquet de origem."""

    if artifact.metadata.kind is not ArtifactKind.EXECUTED:
        raise BenchmarkMetricsError("artefato não é executado")

    frame = artifact.dataframe
    equal = frame["execucoes_iguais"]
    ground_truth_ok = frame["execucao_correta_ground_truth"]
    generated_ok = frame["execucao_correta_generated"]

    correct_mask = equal == True  # noqa: E712 - comparação explícita com o contrato científico
    both_ok_mask = (ground_truth_ok == True) & (generated_ok == True)  # noqa: E712
    error_mask = ~both_ok_mask
    incorrect_without_error_mask = both_ok_mask & ~correct_mask

    # Resultados iguais pressupõem sucesso nas duas execuções. Sem esta relação,
    # uma linha pertenceria simultaneamente a "correct" e "errors".
    if bool((correct_mask & ~both_ok_mask).any()):
        raise BenchmarkMetricsError("igualdade marcada com execução falha")

    total = len(frame)
    correct = int(correct_mask.sum())
    incorrect_without_error = int(incorrect_without_error_mask.sum())
    errors = int(error_mask.sum())
    if correct + incorrect_without_error + errors != total:
        raise BenchmarkMetricsError("partição de resultados incompatível")

    timeouts = int(
        sum(
            is_historical_timeout(message)
            for message in frame.loc[error_mask, "erro_execucao_generated"]
        )
    )
    if timeouts > errors:
        raise BenchmarkMetricsError("timeout fora da partição de erros")

    generation = float(frame["tempo_geracao"].sum())
    execution_ground_truth = float(frame["tempo_execucao_ground_truth"].sum())
    execution_generated = float(frame["tempo_execucao_generated"].sum())
    execution_total = execution_ground_truth + execution_generated
    recorded_total = generation + execution_total

    execution_accuracy = MetricValue(
        key="execution_accuracy",
        value=(correct / total) if total else None,
        available=total > 0,
        numerator=correct,
        denominator=total,
    )
    additional_metrics: list[MetricValue] = []
    for definition in METRIC_REGISTRY:
        if definition.parquet_column is None:
            continue
        values = frame[definition.parquet_column].dropna()
        if any(not math.isfinite(float(value)) for value in values):
            raise BenchmarkMetricsError(
                f"métrica não finita em {definition.parquet_column}"
            )
        denominator = len(values)
        additional_metrics.append(
            MetricValue(
                key=definition.key,
                value=float(values.mean()) if denominator else None,
                available=denominator > 0,
                denominator=denominator,
            )
        )
    return BenchmarkMetrics(
        metrics=(execution_accuracy, *additional_metrics),
        counts=OperationalCounts(
            total=total,
            correct=correct,
            incorrect_without_error=incorrect_without_error,
            errors=errors,
            timeouts=timeouts,
        ),
        times=RecordedTimes(
            generation=generation,
            execution_ground_truth=execution_ground_truth,
            execution_generated=execution_generated,
            execution_total=execution_total,
            recorded_total=recorded_total,
        ),
    )
