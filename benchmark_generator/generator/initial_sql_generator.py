import logging
from typing import Protocol, Annotated

from pydantic import BaseModel

from benchmark_generator.domain.models import QuestionDifficulty, InitialSQL
from benchmark_generator.llm.llm_service import LLMService
from benchmark_generator.llm.prompt_builder import PromptBuilder
from benchmark_generator.util.sql_cleaner import clean_sql


class InitialSQLGeneratorProtocol(Protocol):

    def generate(
            self,
            *,
            schema: str,
            documentation: str | None = None,
            num_difficulties: dict[QuestionDifficulty, int] | None = None,
    ) -> list[InitialSQL]:
        ...


class InitialSQLGenerator(InitialSQLGeneratorProtocol):
    """
    Concrete implementation of InitialSQLGeneratorProtocol that relies on an
    LLM service to generate SQL queries from a schema description.
    """

    def __init__(self, llm_service: "LLMService", prompt_builder: "PromptBuilder"):
        self.llm_service = llm_service
        self.prompt_builder = prompt_builder
        self.logger = logging.getLogger(self.__class__.__name__)

    class SQLEntry(BaseModel):
        sql: str
        difficulty: QuestionDifficulty
        description: Annotated[
            str,
            (
                "Uma descrição em linguagem natural do que a consulta SQL faz semanticamente"
            ),
        ]

    class SQLEntryBatch(BaseModel):
        sqls: list["InitialSQLGenerator.SQLEntry"]

    def generate(
        self,
        *,
        schema: str,
        documentation: str | None = None,
        num_difficulties: dict[QuestionDifficulty, int] | None = None,
    ) -> list[InitialSQL]:
        """
        Generate initial SQL queries using an LLM.

        :param num_queries: Total number of SQL queries to generate.
        :param schema: Database schema description used as context.
        :param documentation: Optional dataset or domain documentation.
        :param num_difficulties: Optional mapping specifying how many queries
                                 should be generated for each difficulty.
        :return: A list of InitialSQL objects.
        """
        self.logger.info(
            "Generating initial SQL queries (difficulty split=%s)",
            num_difficulties,
        )

        prompt = self.prompt_builder.initial_sql_queries_generation_prompt(
            schema=schema,
            documentation=documentation,
            num_difficulties=num_difficulties,
        )

        response = self.llm_service.generate_structured_response(
            prompt=prompt,
            response_model=InitialSQLGenerator.SQLEntryBatch,
        )

        if response is None:
            self.logger.warning("LLM returned no response for initial SQL generation.")
            return []

        return [
            self._to_initial_sql(entry)
            for entry in response.sqls
        ]

    def _to_initial_sql(self, entry: "InitialSQLGenerator.SQLEntry") -> InitialSQL:
        """
        Convert an SQLEntry DTO produced by the LLM into an InitialSQL domain object.

        Removes all SQL comments and normalizes whitespace.

        :param entry: SQLEntry returned by the LLM.
        :return: InitialSQL domain object with cleaned SQL.
        """
        cleaned_sql = clean_sql(entry.sql)
        self.logger.debug(
            "Cleaned SQL: original_len=%d | cleaned_len=%d | preview=%.80s...",
            len(entry.sql),
            len(cleaned_sql),
            cleaned_sql,
        )
        return InitialSQL(
            sql=cleaned_sql,
            dialect="postgresql",
            description=entry.description,
            difficulty=entry.difficulty,
        )