import logging
from pydantic import BaseModel

from benchmark_generator.domain.models import BenchmarkEntry
from benchmark_generator.llm.llm_service import LLMService
from benchmark_generator.llm.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class ParaphraseGenerator:
    """
    Generates paraphrases for an existing benchmark question,
    preserving its semantic intent and SQL metadata.
    """

    def __init__(self, llm_service: LLMService, prompt_builder: PromptBuilder):
        self.llm_service = llm_service
        self.prompt_builder = prompt_builder

    class ParaphraseBatch(BaseModel):
        paraphrases: list[str]

    def generate(
        self,
        entry: BenchmarkEntry,
        *,
        num_paraphrases: int,
    ) -> list[BenchmarkEntry]:
        """
        Generate paraphrases for a given benchmark entry.

        :param entry: The benchmark entry to paraphrase.
        :param num_paraphrases: Number of paraphrases to generate.

        :return: List of new BenchmarkEntry objects with paraphrased questions.
        """
        prompt = self.prompt_builder.paraphrases_generation_prompt(
            question=entry.question,
            num_paraphrases=num_paraphrases,
        )

        response = self.llm_service.generate_structured_response(
            prompt=prompt,
            response_model=ParaphraseGenerator.ParaphraseBatch,
        )

        return [
            BenchmarkEntry(
                dataset_id=entry.dataset_id,
                question=p,
                difficulty=entry.difficulty,
                query_patterns=entry.query_patterns,
                tables=entry.tables,
                evidence=entry.evidence,
                sql=entry.sql,
            )
            for p in response.paraphrases
        ]