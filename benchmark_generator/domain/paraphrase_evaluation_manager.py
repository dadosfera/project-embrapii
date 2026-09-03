from typing import Iterable
from benchmark_generator.domain.models import (
    BenchmarkEntry,
    ParaphraseEvaluation,
)
from benchmark_generator.evaluation.bleu_evaluator import BLEUParaphraseEvaluator
from benchmark_generator.evaluation.cross_encoder_evaluator import CrossEncoderParaphraseEvaluator
from benchmark_generator.evaluation.paraphrase_evaluator import ParaphraseEvaluator
from benchmark_generator.evaluation.sbert_evaluator import SBERTParaphraseEvaluator
from benchmark_generator.util import get_logger


class ParaphraseEvaluationManager:
    """
    Coordinates the evaluation of paraphrased questions
    against their parent questions using multiple evaluators.
    """

    def __init__(
            self,
            evaluators: list[ParaphraseEvaluator] | None = None,
     ):
        self._evaluators = evaluators or [
            BLEUParaphraseEvaluator(),
            SBERTParaphraseEvaluator(),
            CrossEncoderParaphraseEvaluator()
        ]
        self.logger = get_logger("ParaphraseEvaluationManager")

    def evaluate(
        self,
        *,
        parent: BenchmarkEntry,
        child: BenchmarkEntry,
    ) -> list[ParaphraseEvaluation]:
        evaluations: list[ParaphraseEvaluation] = []

        for evaluator in self._evaluators:
            result = evaluator.evaluate(parent=parent, child=child)

            evaluation = ParaphraseEvaluation(
                parent_id=parent.id,
                child_id=child.id,
                method=result.method,
                score=result.score,
                parent_question=parent.question,
                child_question=child.question,
                details=result.details,
            )

            evaluations.append(evaluation)

            self.logger.info(
                "Evaluation %s | score=%.4f",
                result.method,
                result.score,
            )

        return evaluations