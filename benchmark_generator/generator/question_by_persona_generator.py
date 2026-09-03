from concurrent.futures import ThreadPoolExecutor
from typing import Protocol, Annotated
import logging

from pydantic import BaseModel

from benchmark_generator import BenchmarkEntry
from benchmark_generator.domain.models import Persona, DetailedSQL
from benchmark_generator.llm.llm_service import LLMService
from benchmark_generator.llm.prompt_builder import PromptBuilder

class QuestionByPersonaGeneratorProtocol(Protocol):

    def generate(
            self,
            generated_sql: DetailedSQL | list[DetailedSQL],
            personas: list[Persona]
    ) -> list[BenchmarkEntry]:
        ...

class QuestionByPersonaGenerator(QuestionByPersonaGeneratorProtocol):

    def __init__(self, llm_service: "LLMService", prompt_builder: "PromptBuilder", dataset_id: str):
        self.llm_service = llm_service
        self.prompt_builder = prompt_builder
        self.logger = logging.getLogger(self.__class__.__name__)
        self.dataset_id = dataset_id

    class QuestionPersonaPair(BaseModel):
        question: str
        persona: Annotated[
            str,
            "The persona role of the question"
        ]

    class PossibleQuestions(BaseModel):
        questions: list["QuestionByPersonaGenerator.QuestionPersonaPair"]

    def generate(
            self,
            generated_sql: DetailedSQL | list[DetailedSQL],
            personas: list[Persona]
    ) -> list[BenchmarkEntry]:

        if isinstance(generated_sql, DetailedSQL):
            sqls = [generated_sql]
        else:
            sqls = generated_sql

        self.logger.info(
            "Generating questions for %d personas (number of sqls: %d)",
            len(personas),
            len(sqls),
        )

        all_entries: list[BenchmarkEntry] = []

        with ThreadPoolExecutor(thread_name_prefix="persona-generator") as pool:
            # Preserve submission order by keeping an ordered list of futures.
            futures = [
                pool.submit(self._generate_for_sql, sql, personas)
                for sql in sqls
            ]
            self.logger.debug(
                "Submitted %d persona generation tasks to thread pool.", len(futures)
            )
            for future in futures:
                all_entries.extend(future.result())

        return all_entries

    def _generate_for_sql(
            self,
            sql: DetailedSQL,
            personas: list[Persona],
    ) -> list[BenchmarkEntry]:
        """
        Generates persona-based questions for a single :class:`DetailedSQL` entry.

        Performs one LLM call and maps each returned question/persona pair to a
        :class:`BenchmarkEntry`.

        :param sql: The SQL entry to generate questions for.
        :param personas: List of personas passed to the prompt.
        :return: List of generated :class:`BenchmarkEntry` objects.
        """
        prompt = self.prompt_builder.sql_to_question_by_persona_generation_prompt(
            generated_sql=sql.sql,
            sql_description=sql.description,
            personas=personas,
        )

        self.logger.debug(
            "Calling LLM for sql (difficulty=%s, tables=%s): %.60s...",
            sql.difficulty,
            sql.tables,
            sql.sql,
        )

        response = self.llm_service.generate_structured_response(
            prompt=prompt,
            response_model=QuestionByPersonaGenerator.PossibleQuestions,
        )

        self.logger.info(
            "LLM returned %d question(s) for sql: %.60s...",
            len(response.questions),
            sql.sql,
        )

        entries: list[BenchmarkEntry] = []
        for question_pair in response.questions:
            persona = next((p for p in personas if p.role == question_pair.persona), None)
            self.logger.debug(
                "  → persona='%s' | question='%.80s...'",
                question_pair.persona,
                question_pair.question,
            )
            if persona is None:
                self.logger.warning(
                    "Persona role '%s' not found in provided personas list — entry will have persona=None.",
                    question_pair.persona,
                )
            entries.append(BenchmarkEntry(
                dataset_id=self.dataset_id,
                question=question_pair.question,
                difficulty=sql.difficulty,
                query_patterns=sql.query_patterns,
                tables=sql.tables,
                sql=sql.sql,
                persona=persona,
            ))

        self.logger.debug(
            "Mapped %d entr%s for sql: %.50s...",
            len(entries),
            "y" if len(entries) == 1 else "ies",
            sql.sql,
        )
        return entries





