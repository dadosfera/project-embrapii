import logging
from typing import Annotated

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from benchmark_generator.domain.models import (
    QueryPattern,
    QuestionDifficulty,
    BenchmarkEntry, Dataset,
)
from benchmark_generator.llm.context import default_llm_context
from benchmark_generator.llm.prompt_builder import PromptBuilder
from benchmark_generator.llm.llm_service import LLMService, OpenAIService

logger = logging.getLogger(__name__)
load_dotenv()


class QuestionGenerator:
    """
    Generates natural language questions for Text-to-SQL benchmarks
    given a dataset schema.
    """

    def __init__(
        self,
        llm_service: LLMService = default_llm_context.llm_service,
        prompt_builder: PromptBuilder = default_llm_context.prompt_builder,
    ):
        self.llm_service = llm_service
        self.prompt_builder = prompt_builder
        self.logger = logging.getLogger("QuestionGenerator")

    class QuestionDraft(BaseModel):
        question: str
        difficulty: QuestionDifficulty
        query_patterns: list[QueryPattern]
        tables: Annotated[list[str], Field(description="Tables involved")]
        evidence: str | None = None

    class QuestionBatch(BaseModel):
        questions: list["QuestionGenerator.QuestionDraft"]

    def generate(
        self,
        *,
        dataset: Dataset,
        num_questions: int,
    ) -> list[BenchmarkEntry]:
        """
        Generate natural language questions for a given dataset schema.

        :param sql_schema: The SQL schema of the dataset.
        :param dataset_id: Identifier for the dataset.
        :param num_questions: Number of questions to generate.

        :return: List of generated BenchmarkEntry objects.
        """
        logger.info(
            "Generating %d questions for %s",
            num_questions,
            dataset.id
        )

        prompt = self.prompt_builder.initial_questions_generation_prompt(
            sql_schema=dataset.schema,
            num_questions=num_questions,
        )

        response = self.llm_service.generate_structured_response(
            prompt=prompt,
            response_model=QuestionGenerator.QuestionBatch,
        )

        return [
            BenchmarkEntry(
                dataset_id=dataset.id,
                question=q.question,
                difficulty=q.difficulty,
                query_patterns=q.query_patterns,
                tables=q.tables,
                evidence=q.evidence,
            )
            for q in response.questions
        ]