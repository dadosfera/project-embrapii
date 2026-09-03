from sentence_transformers import SentenceTransformer, util

from benchmark_generator.domain.models import BenchmarkEntry, ParaphraseEvaluation
from benchmark_generator.evaluation.evaluation_result import EvaluationResult
from benchmark_generator.evaluation.paraphrase_evaluator import ParaphraseEvaluator
from benchmark_generator.util import get_logger


class SBERTParaphraseEvaluator(ParaphraseEvaluator):
    """
    Evaluates semantic similarity between two questions using SBERT
    cosine similarity over sentence embeddings.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        normalize_embeddings: bool = True,
    ):
        """
        :param model_name: SBERT model identifier
        :param normalize_embeddings: Whether to L2-normalize embeddings
        """
        self.model = SentenceTransformer(model_name)
        self.normalize_embeddings = normalize_embeddings
        self.logger = get_logger("SBERTParaphraseEvaluator")

        self.logger.info(
            "Initialized SBERT evaluator with model %s",
            model_name,
        )

    def evaluate(
        self,
        *,
        parent: BenchmarkEntry,
        child: BenchmarkEntry,
    ) -> ParaphraseEvaluation:
        """
        Compute cosine similarity between parent and child questions.

        :return: EvaluationResult with cosine similarity score
        """
        sentences = [parent.question, child.question]

        embeddings = self.model.encode(
            sentences,
            convert_to_tensor=True,
            normalize_embeddings=self.normalize_embeddings,
        )

        score = util.cos_sim(embeddings[0], embeddings[1]).item()

        self.logger.debug(
            "SBERT similarity (%s → %s): %.4f",
            parent.id,
            child.id,
            score,
        )

        return ParaphraseEvaluation(
            parent_id=parent.id,
            child_id=child.id,
            method="sbert_cosine_similarity",
            score=score,
            parent_question=parent.question,
            child_question=child.question
        )