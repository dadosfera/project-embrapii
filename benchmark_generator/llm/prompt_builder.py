from jinja2 import Environment, BaseLoader

from benchmark_generator.domain.models import BenchmarkEntry, QuestionDifficulty, Persona
from benchmark_generator.llm.prompt.loader.loaders import FilePromptLoader
from benchmark_generator.llm.prompt.loader.protocol import PromptLoader


class PromptBuilder:

    def __init__(
            self,
            loader: PromptLoader | None = None,
            locale: str = "pt_BR"
    ):
        self.loader = loader or FilePromptLoader()
        self.locale = locale
        self._jinja_env = Environment(loader=BaseLoader())

    def initial_questions_generation_prompt(
            self,
            sql_schema: str,
            num_questions: int
    ) -> str:
        return self._render(
            "initial_questions_generation",
            sql_schema=sql_schema,
            num_questions=num_questions
        )

    def paraphrases_generation_prompt(
        self,
        *,
        question: str,
        num_paraphrases: int
    ) -> str:
        return self._render(
            "paraphrases_generation",
            question=question,
            num_paraphrases=num_paraphrases
        )

    def sql_from_question_generation_prompt(
        self,
        *,
        question: str,
        schema: str,
        documentation: str | None = None,
        hint: str | None = None,
        sql_dialect: str | None = None,
    ) -> str:
        return self._render(
            "sql_from_question_generation",
            question=question,
            schema=schema,
            documentation=documentation,
            hint=hint,
            sql_dialect=sql_dialect
        )

    def sql_rewrite_for_paraphrase_prompt(
        self,
        original_question: str,
        entry: BenchmarkEntry,
        sql_dialect: str | None = None,
    ) -> str:
        tables = ", ".join(entry.tables) if entry.tables else None
        patterns = ", ".join(entry.query_patterns) if entry.query_patterns else None
        difficulty = entry.difficulty

        if not entry.sql:
            raise ValueError(
                "SQL generation requires a reference SQL in BenchmarkEntry.sql"
            )

        return self._render(
            "sql_rewrite_for_paraphrase",
            original_question=original_question,
            entry=entry,
            tables=tables,
            patterns=patterns,
            difficulty=difficulty,
            sql_dialect=sql_dialect
        )

    def initial_sql_queries_generation_prompt(
            self,
            *,
            schema: str,
            documentation: str | None,
            num_difficulties: dict[QuestionDifficulty, int] | None,
    ) -> str:
        difficulties_block = ""
        if num_difficulties:
            difficulties_block = "\n".join(
                f"- {difficulty}: {count} queries"
                for difficulty, count in num_difficulties.items()
            )

        return self._render(
            "initial_sql_queries_generation",
            schema=schema,
            documentation=documentation,
            difficulties_block=difficulties_block
        )

    def sql_to_question_by_persona_generation_prompt(
            self,
            *,
            generated_sql: str,
            sql_description: str,
            personas: list[Persona]
    ) -> str:
        return self._render(
            "sql_to_question_by_persona_generation",
            generated_sql=generated_sql,
            sql_description=sql_description,
            personas=personas
        )

    def sql_error_correction_prompt(
            self,
            *,
            generated_sql: str,
            sql_error: str,
            schema: str | None = None,
            documentation: str | None = None,
            sql_dialect: str | None = None,
    ):
        return self._render(
            "sql_error_correction",
            generated_sql=generated_sql,
            sql_error=sql_error,
            schema=schema,
            documentation=documentation,
            sql_dialect=sql_dialect
        )

    ### Util Methods

    def _render(self, template_name: str, **kwargs) -> str:
        raw = self.loader.load(template_name, self.locale)
        template = self._jinja_env.from_string(raw)
        return template.render(**kwargs)