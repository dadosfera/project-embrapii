from typing import Annotated

from pydantic import BaseModel

from benchmark_generator import BenchmarkEntry
from benchmark_generator.llm.context import default_llm_context
from benchmark_generator.llm.llm_service import LLMService
from benchmark_generator.llm.prompt_builder import PromptBuilder


class SQLRewriterForParaphrase:

    def __init__(
            self,
            llm_service: LLMService = default_llm_context.llm_service,
            prompt_builder: PromptBuilder = default_llm_context.prompt_builder,
    ):
        self.llm_service = llm_service
        self.prompt_builder = prompt_builder

    class RewrittenSQLDraft(BaseModel):
        sql: Annotated[
            str,
            "The rewritten SQL query corresponding to the paraphrased natural language question."
        ]

    def generate(
        self,
        orginal_question: str,
        entry: BenchmarkEntry,
        sql_dialect: str | None = None,
    ) -> str:
        """
        Generate a corrected SQL query for a paraphrased question based on the original question and SQL.

        :param entry: The benchmark entry containing the paraphrased question and original SQL.
        """

        prompt = self.prompt_builder.sql_rewrite_for_paraphrase_prompt(orginal_question, entry, sql_dialect=sql_dialect)

        response = self.llm_service.generate_structured_response(
            prompt=prompt,
            response_model=SQLRewriterForParaphrase.RewrittenSQLDraft,
        )

        return response.sql.strip()
