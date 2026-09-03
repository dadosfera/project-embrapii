from typing import Protocol
from benchmark_generator.domain.models import BenchmarkEntry, ParaphraseEvaluation


class ParaphraseEvaluator(Protocol):
    """
    Protocol for paraphrase similarity evaluators.
    """

    def evaluate(
        self,
        *,
        parent: BenchmarkEntry,
        child: BenchmarkEntry,
    ) -> ParaphraseEvaluation:
        ...