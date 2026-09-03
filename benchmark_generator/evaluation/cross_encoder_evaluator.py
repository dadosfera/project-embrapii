from sentence_transformers import CrossEncoder

from benchmark_generator.domain.models import BenchmarkEntry, ParaphraseEvaluation
from benchmark_generator.evaluation.evaluation_result import EvaluationResult
from benchmark_generator.evaluation.paraphrase_evaluator import ParaphraseEvaluator
from benchmark_generator.util import get_logger


class CrossEncoderParaphraseEvaluator(ParaphraseEvaluator):
    """
    Evaluates semantic similarity using a Cross-Encoder model.
    This method jointly encodes the sentence pair and outputs
    a similarity score.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/stsb-roberta-base",
        device: str | None = None,
    ):
        """
        :param model_name: Cross-Encoder model identifier
        :param device: Torch device override (e.g., "cpu", "cuda")
        """
        self.model = CrossEncoder(
            model_name,
            device=device,
        )
        self.logger = get_logger("CrossEncoderParaphraseEvaluator")

        self.logger.info(
            "Initialized Cross-Encoder evaluator with model %s",
            model_name,
        )

    def evaluate(
        self,
        *,
        parent: BenchmarkEntry,
        child: BenchmarkEntry,
    ) -> ParaphraseEvaluation:
        """
        Compute semantic similarity score using a cross-encoder.

        :return: EvaluationResult with cross-encoder score
        """
        pair = [(parent.question, child.question)]

        result = self.model.predict(pair)
        self.logger.debug("Cross-Encoder raw result: %s", result)

        score = float(result[0])

        self.logger.debug(
            "Cross-Encoder similarity (%s → %s): %.4f",
            parent.id,
            child.id,
            score,
        )

        return ParaphraseEvaluation(
            parent_id=parent.id,
            child_id=child.id,
            method="cross_encoder",
            score=score,
            parent_question=parent.question,
            child_question=child.question
        )