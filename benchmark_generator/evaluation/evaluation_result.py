from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationResult:
    """
    Result of a similarity evaluation between two benchmark entries.
    """
    method: str
    score: float
    details: dict[str, float] | None = None