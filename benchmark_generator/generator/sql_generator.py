# benchmark_generator/generator/sql_generator.py
import logging
from typing import Annotated

from pydantic import BaseModel

from benchmark_generator.domain.models import BenchmarkEntry, Dataset
from benchmark_generator.llm.llm_service import LLMService
from benchmark_generator.llm.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class SQLGenerator:
    """
    Generates SQL queries for an existing benchmark question
    given the dataset schema.
    """

    def __init__(self, llm_service: LLMService, prompt_builder: PromptBuilder):
        self.llm_service = llm_service
        self.prompt_builder = prompt_builder

    class SQLDraft(BaseModel):
        sql: Annotated[
            str,
            "The SQL query corresponding to the provided natural language question."
        ]

    def generate(
        self,
        *,
        entry: BenchmarkEntry,
        dataset: Dataset,
        hint: str | None = None,
        sql_dialect: str | None = None,
    ) -> str:

        prompt = self.prompt_builder.sql_from_question_generation_prompt(
            question=entry.question,
            schema=dataset.schema,
            documentation=dataset.documentation,
            hint=hint,
            sql_dialect=sql_dialect
        )

        response = self.llm_service.generate_structured_response(
            prompt=prompt,
            response_model=SQLGenerator.SQLDraft,
        )

        return response.sql.strip()