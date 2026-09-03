from typing import Annotated

from pydantic import BaseModel

from benchmark_generator.llm.context import default_llm_context
from benchmark_generator.llm.llm_service import LLMService
from benchmark_generator.llm.prompt_builder import PromptBuilder


class SQLErrorCorrector:

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
            "The corrected SQL query"
        ]

    def generate(
        self,
        generated_sql: str,
        error_message: str,
        schema: str | None = None,
        documentation: str | None = None,
        sql_dialect: str | None = None,
    ) -> str:
        """
        Generate a corrected SQL query for a paraphrased question based on the original question and SQL.
        """

        prompt = self.prompt_builder.sql_error_correction_prompt(
            generated_sql=generated_sql,
            sql_error=error_message,
            schema=schema,
            documentation=documentation,
            sql_dialect=sql_dialect
        )

        response = self.llm_service.generate_structured_response(
            prompt=prompt,
            response_model=SQLErrorCorrector.RewrittenSQLDraft,
        )

        return response.sql.strip()
