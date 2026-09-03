from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

from benchmark_generator.domain.models import BenchmarkEntry, ParaphraseEvaluation
from benchmark_generator.evaluation.paraphrase_evaluator import ParaphraseEvaluator
from benchmark_generator.evaluation.evaluation_result import EvaluationResult
from benchmark_generator.util import get_logger


class BLEUParaphraseEvaluator(ParaphraseEvaluator):
    """
    Evaluator that uses BLEU score to assess similarity between paraphrased questions.
    """

    def __init__(self, smoothing_function: SmoothingFunction = SmoothingFunction().method4):
        self.smoothing_function = smoothing_function
        self.logger = get_logger("BLEUParaphraseEvaluator")

        self.logger.info("Initialized BLEU Paraphrase Evaluator with smoothing function: %s", smoothing_function.__name__)

    def evaluate(
        self,
        *,
        parent: BenchmarkEntry,
        child: BenchmarkEntry,
    ) -> ParaphraseEvaluation:
        """
        Evaluate the similarity between the parent and child benchmark entries using the BLEU score.
        """

        reference = parent.question.split()
        candidate = child.question.split()

        bleu_score = sentence_bleu(
            [reference],
            candidate,
            smoothing_function=self.smoothing_function
        )

        return ParaphraseEvaluation(
            parent_id=parent.id,
            child_id=child.id,
            method="bleu",
            score=bleu_score,
            parent_question=parent.question,
            child_question=child.question,
        )