import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable

from benchmark_generator.domain.models import (
    BenchmarkEntry, QuestionDifficulty, QueryPattern, Dataset,
    ParaphraseEvaluation, Persona, DetailedSQL, ValidationResult,
)
from benchmark_generator.domain.paraphrase_evaluation_manager import ParaphraseEvaluationManager
from benchmark_generator.domain.sql_repository import SQLRepository
from benchmark_generator.generator import QuestionGenerator
from benchmark_generator.generator.initial_sql_generator import InitialSQLGeneratorProtocol
from benchmark_generator.generator.paraphrase_generator import ParaphraseGenerator
from benchmark_generator.generator.question_by_persona_generator import QuestionByPersonaGenerator
from benchmark_generator.generator.sql_rewriter_for_paraphrase import SQLRewriterForParaphrase
from benchmark_generator.generator.sql_generator import SQLGenerator
from benchmark_generator.infra.sql_validation.sql_validator import SQLValidator
from benchmark_generator.persistence import BenchmarkRepository
from benchmark_generator.persistence.paraphrase_evaluation_repository import ParaphraseEvaluationRepository
from benchmark_generator.sql_analysis.detailer import SQLDetailer
from benchmark_generator.util import get_logger


class BenchmarkManager:
    """
    Orchestrates the construction and maintenance of a collection
    of benchmark questions and their associated metadata.

    This class acts as the aggregate root for the benchmark domain,
    centralizing all operations related to:

    - Question generation
    - Question lifecycle management
    - SQL generation, validation, and attachment
    - Paraphrase generation and evaluation
    - Persistence delegation

    Every SQL query produced by any generation step is validated through
    :class:`SQLValidator` before being accepted into the benchmark set.
    Invalid queries are silently discarded and logged.
    """

    def __init__(
        self,
        question_generator: QuestionGenerator,
        paraphrase_generator: ParaphraseGenerator,
        initial_sql_generator: InitialSQLGeneratorProtocol,
        sql_rewriter: SQLRewriterForParaphrase,
        sql_generator: SQLGenerator,
        question_by_persona_generator: QuestionByPersonaGenerator,
        sql_validator: SQLValidator,
        paraphrase_evaluation_manager_factory: Callable[[], ParaphraseEvaluationManager],
        sql_dialect: str | None = None,
    ):
        self._questions: list[BenchmarkEntry] = []
        self._question_generator = question_generator
        self._sql_queries: list[DetailedSQL] = []

        self._initial_sql_generator = initial_sql_generator
        self._paraphrase_generator = paraphrase_generator
        self._sql_generator = sql_generator
        self._sql_rewriter = sql_rewriter
        self._question_by_persona_generator = question_by_persona_generator
        self._sql_validator = sql_validator

        self._paraphrase_evaluation_manager_factory = paraphrase_evaluation_manager_factory
        self._paraphrase_evaluation_manager_instance: ParaphraseEvaluationManager | None = None

        self._evaluations: list[ParaphraseEvaluation] = []

        self._sql_dialect = sql_dialect
        self.logger = get_logger("BenchmarkManager")

    #
    # Generation
    #

    def generate_questions(
        self,
        dataset: Dataset,
        num_questions: int,
    ) -> list[BenchmarkEntry]:
        """
        Generate new benchmark questions using the configured generator.

        :param dataset: Dataset containing db_id and schema text.
        :param num_questions: Number of questions to generate.
        :return: List of newly generated :class:`BenchmarkEntry` objects.
        """
        self.logger.info(
            "Starting generation of %d questions for %s",
            num_questions,
            dataset.id,
        )

        try:
            new_questions = self._question_generator.generate(
                dataset=dataset,
                num_questions=num_questions,
            )

            self._questions.extend(new_questions)
            self.logger.info(
                "Successfully generated %d questions. Total: %d",
                len(new_questions),
                len(self._questions),
            )

            return new_questions

        except Exception as e:
            self.logger.error("Error generating questions: %s", e, exc_info=True)
            raise

    def generate_sql_queries(
        self,
        index: int | set[int] | list[int],
        dataset: Dataset,
    ) -> None:
        """
        Generate and validate SQL queries for specific benchmark questions.

        Only queries that pass :class:`SQLValidator` validation are attached
        to the corresponding :class:`BenchmarkEntry`. Invalid queries are
        discarded with a warning log.

        :param index: Index or collection of indices of questions to generate SQL for.
        :param dataset: Dataset to help with SQL generation.
        """
        indices = self._normalize_indices(index)

        for i in indices:
            self._validate_index(i)
            entry = self._questions[i]

            if entry.dataset_id != dataset.id:
                raise ValueError(
                    f"Dataset ID mismatch for question at index {i}: "
                    f"expected {entry.dataset_id}, got {dataset.id}"
                )

            self.logger.info(
                "Generating SQL for question at index %d: %.50s...",
                i,
                entry.question,
            )

            try:
                generated_sql = self._sql_generator.generate(
                    entry=entry,
                    dataset=dataset,
                    hint=entry.evidence,
                    sql_dialect=self._sql_dialect,
                )

                result = self._sql_validator.validate(generated_sql)

                if result.is_valid:
                    entry.sql = result.final_query
                    self.logger.info(
                        "Validated SQL for index %d: %.50s...",
                        i,
                        result.final_query,
                    )
                else:
                    self.logger.warning(
                        "SQL for index %d discarded after validation: %s",
                        i,
                        result.message,
                    )

            except Exception as e:
                self.logger.error(
                    "Error generating SQL for index %d: %s",
                    i,
                    e,
                    exc_info=True,
                )
                raise

    def generate_initial_sql_queries(
        self,
        dataset: Dataset,
        num_queries: int | None = None,
        difficulties: dict[QuestionDifficulty, int] | None = None,
        append: bool = True,
    ) -> None:
        """
        Generate an initial set of SQL queries for the dataset.

        Each generated query is validated through :class:`SQLValidator`.
        Only valid queries are retained in the internal collection.

        :param dataset: Target dataset.
        :param num_queries: Total number of queries (split equally across difficulties).
        :param difficulties: Explicit difficulty → count mapping.
        :param append: Whether to append to the existing collection or replace it.
        :raises ValueError: If neither or both of *num_queries* / *difficulties* are provided.
        """
        if num_queries is None and difficulties is None:
            raise ValueError("Either num_queries or difficulties must be provided")
        if num_queries is not None and difficulties is not None:
            raise ValueError("Only one of num_queries or difficulties can be provided")

        if num_queries is not None:
            difficulties = {
                "easy": math.ceil(num_queries / 3),
                "medium": math.ceil(num_queries / 3),
                "hard": math.ceil(num_queries / 3),
            }

        self.logger.info(
            "Generating initial SQL queries for dataset %s with difficulty distribution: %s",
            dataset.id,
            difficulties,
        )

        try:
            initial_sqls = self._initial_sql_generator.generate(
                schema=dataset.schema,
                num_difficulties=difficulties,
            )

            detailed_sqls = [SQLDetailer().detail(e) for e in initial_sqls]

            def _validate_entry(entry: DetailedSQL) -> tuple[DetailedSQL, ValidationResult]:
                return entry, self._sql_validator.validate(entry.sql)

            valid_sqls: list[DetailedSQL] = []
            with ThreadPoolExecutor(thread_name_prefix="sql-validator") as pool:
                futures = {pool.submit(_validate_entry, entry): entry for entry in detailed_sqls}
                self.logger.debug(
                    "Submitted %d SQL validation tasks to thread pool.", len(futures)
                )
                for future in as_completed(futures):
                    sql_entry, result = future.result()
                    if result.is_valid:
                        sql_entry.sql = result.final_query
                        valid_sqls.append(sql_entry)
                    else:
                        self.logger.warning(
                            "Initial SQL discarded: %s | reason: %s",
                            sql_entry.sql,
                            result.message,
                        )

            self._sql_queries = valid_sqls if not append else self._sql_queries + valid_sqls

            self.logger.info(
                "Generated %d initial SQL queries, %d passed validation",
                len(initial_sqls),
                len(valid_sqls),
            )

        except Exception as e:
            self.logger.error("Error generating initial SQL queries: %s", e, exc_info=True)
            raise

    def generate_questions_by_persona(
        self,
        generated_sqls: DetailedSQL | list[DetailedSQL],
        personas: list[Persona],
        validate_sql_queries: bool = True,
    ) -> list[BenchmarkEntry]:
        """
        Generate questions for specific personas based on generated SQLs.

        SQL attached to each resulting entry is re-validated. Entries whose
        SQL fails validation have their ``sql`` field set to ``None``.

        :param generated_sqls: Single or list of :class:`DetailedSQL` objects.
        :param personas: List of :class:`Persona` objects to generate questions for.
        :return: List of generated :class:`BenchmarkEntry` objects.
        """
        self.logger.info("Generating questions for %d personas", len(personas))

        try:
            new_questions = self._question_by_persona_generator.generate(
                generated_sql=generated_sqls,
                personas=personas,
            )

            if validate_sql_queries:
                for entry in new_questions:
                    if entry.sql:
                        result = self._sql_validator.validate(entry.sql)
                        if result.is_valid:
                            entry.sql = result.final_query
                        else:
                            self.logger.warning(
                                "SQL for persona question discarded: %s",
                                result.message,
                            )
                            entry.sql = None

            self._questions.extend(new_questions)
            self.logger.info(
                "Successfully generated %d questions by persona. Total: %d",
                len(new_questions),
                len(self._questions),
            )

            return new_questions

        except Exception as e:
            self.logger.error(
                "Error generating questions by persona: %s",
                e,
                exc_info=True,
            )
            raise

    #
    # Paraphrasing
    #

    def paraphrase_question(
        self,
        index: int,
        *,
        num_paraphrases: int,
        append: bool = True,
    ) -> list[BenchmarkEntry]:
        """
        Generate paraphrases for a specific benchmark question.

        Each paraphrase preserves the original intent and metadata,
        differing only in the natural language formulation. The SQL is
        rewritten via :class:`SQLRewriterForParaphrase` and validated
        through :class:`SQLValidator`. Paraphrases whose rewritten SQL
        fails validation have their ``sql`` field set to ``None``.

        :param index: Index of the question to paraphrase.
        :param num_paraphrases: Number of paraphrases to generate.
        :param append: Whether to append paraphrases to the benchmark.
        :return: List of newly created :class:`BenchmarkEntry` instances.
        :raises IndexError: If the index is out of range.
        """
        self._validate_index(index)
        original = self._questions[index]

        self.logger.info(
            "Generating %d paraphrases for question at index %d",
            num_paraphrases,
            index,
        )

        try:
            paraphrases = self._paraphrase_generator.generate(
                original,
                num_paraphrases=num_paraphrases,
            )

            new_entries: list[BenchmarkEntry] = []

            for new_entry in paraphrases:
                new_entry.parent_id = original.id

                rewritten_sql = self._sql_rewriter.generate(
                    original.question,
                    new_entry,
                    sql_dialect=self._sql_dialect,
                )

                result = self._sql_validator.validate(rewritten_sql)
                if result.is_valid:
                    new_entry.sql = result.final_query
                    self.logger.info(
                        "Rewritten SQL validated for paraphrase: %.50s...",
                        result.final_query,
                    )
                else:
                    self.logger.warning(
                        "Rewritten SQL discarded for paraphrase: %s",
                        result.message,
                    )
                    new_entry.sql = None

                new_entries.append(new_entry)

            if append:
                self._questions.extend(new_entries)
                self.logger.info(
                    "Appended %d paraphrased questions (total: %d)",
                    len(new_entries),
                    len(self._questions),
                )

            return new_entries

        except Exception as e:
            self.logger.error(
                "Error generating paraphrases for index %d: %s",
                index,
                e,
                exc_info=True,
            )
            raise

    #
    # Evaluation
    #

    def evaluate_paraphrase(
        self,
        parent_index: int,
        child_index: int | set[int] | None = None,
    ) -> list[ParaphraseEvaluation]:
        """
        Evaluate the similarity between a parent question and one or more children.

        When *child_index* is ``None``, all questions whose ``parent_id``
        matches the parent question's id are evaluated.

        :param parent_index: Index of the parent question.
        :param child_index: Optional index or set of indices of child questions.
        :return: List of :class:`ParaphraseEvaluation` objects.
        """
        self._validate_index(parent_index)
        parent = self._questions[parent_index]
        children = self._get_children(parent, child_index)

        new_evaluations: list[ParaphraseEvaluation] = []

        for child in children:
            evaluations = self._paraphrase_evaluation_manager.evaluate(
                parent=parent,
                child=child,
            )
            new_evaluations.extend(evaluations)

        self._evaluations.extend(new_evaluations)

        self.logger.info(
            "Stored %d new paraphrase evaluations (total: %d)",
            len(new_evaluations),
            len(self._evaluations),
        )

        return new_evaluations

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def list_questions(self) -> list[BenchmarkEntry]:
        """Return all benchmark questions."""
        return list(self._questions)

    def count(self) -> int:
        """Return the total number of questions in the benchmark."""
        return len(self._questions)

    def clear(self) -> None:
        """Remove all questions from the benchmark."""
        self._questions.clear()

    def add_question(self, question: BenchmarkEntry) -> None:
        """
        Add an existing :class:`BenchmarkEntry` to the benchmark.

        :param question: Entry to be added.
        """
        self._questions.append(question)
        self.logger.debug("Added question: %.50s...", question.question)

    def delete_question(self, index: int) -> None:
        """
        Remove a question from the benchmark by index.

        :param index: Index of the question to remove.
        :raises IndexError: If the index is out of range.
        """
        self._validate_index(index)
        deleted = self._questions.pop(index)
        self.logger.info(
            "Deleted question at index %d: %.50s...",
            index,
            deleted.question,
        )

    def update_question(
        self,
        index: int,
        *,
        question: Optional[str] = None,
        difficulty: Optional[QuestionDifficulty] = None,
        query_patterns: Optional[list[QueryPattern]] = None,
        tables: Optional[list[str]] = None,
        evidence: Optional[str] = None,
        sql: Optional[str] = None,
    ) -> None:
        """
        Update attributes of an existing benchmark entry.

        Only explicitly provided (non-``None``) attributes are updated.

        :param index: Index of the question to update.
        :param question: Updated natural language question.
        :param difficulty: Updated difficulty level.
        :param query_patterns: Updated query pattern annotations.
        :param tables: Updated list of related tables.
        :param evidence: Updated evidence or domain rationale.
        :param sql: Updated SQL string (validated before assignment).
        :raises IndexError: If the index is out of range.
        """
        self._validate_index(index)
        q = self._questions[index]

        if question is not None:
            q.question = question
        if difficulty is not None:
            q.difficulty = difficulty
        if query_patterns is not None:
            q.query_patterns = query_patterns
        if tables is not None:
            q.tables = tables
        if evidence is not None:
            q.evidence = evidence
        if sql is not None:
            result = self._sql_validator.validate(sql.strip())
            if result.is_valid:
                q.sql = result.final_query
            else:
                self.logger.warning(
                    "SQL update for index %d rejected: %s",
                    index,
                    result.message,
                )

        self.logger.info("Updated question at index %d", index)

    def list_evaluations(self) -> list[ParaphraseEvaluation]:
        """Return all paraphrase evaluations."""
        return list(self._evaluations)

    def clear_evaluations(self) -> None:
        """Remove all paraphrase evaluations."""
        self._evaluations.clear()

    def list_sql_queries(self) -> list[DetailedSQL]:
        """Return all generated SQL queries."""
        return list(self._sql_queries)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load_questions(self, repository: BenchmarkRepository) -> None:
        """
        Load benchmark questions from a repository.

        :param repository: Repository implementation responsible for loading.
        :raises FileNotFoundError: If the underlying data source does not exist.
        """
        try:
            self._questions = repository.load()
            self.logger.info(
                "Loaded %d questions successfully",
                len(self._questions),
            )
        except FileNotFoundError:
            self.logger.warning("No existing questions file found")
            raise
        except Exception as e:
            self.logger.error("Error loading questions: %s", e, exc_info=True)
            raise

    def save_questions(self, repository: BenchmarkRepository) -> None:
        """
        Save all benchmark questions to a repository.

        :param repository: Repository implementation responsible for saving.
        """
        self.logger.info("Saving %d questions to repository", len(self._questions))
        try:
            repository.save(self._questions)
            self.logger.info("Questions saved successfully")
        except Exception as e:
            self.logger.error("Error saving questions: %s", e, exc_info=True)
            raise

    def load_evaluations(self, repository: ParaphraseEvaluationRepository) -> None:
        """
        Load paraphrase evaluations from a repository.

        :param repository: Repository implementation responsible for loading.
        :raises FileNotFoundError: If the underlying data source does not exist.
        """
        try:
            self._evaluations = repository.load()
            self.logger.info(
                "Loaded %d paraphrase evaluations successfully",
                len(self._evaluations),
            )
        except FileNotFoundError:
            self.logger.warning("No existing evaluations file found")
            raise
        except Exception as e:
            self.logger.error("Error loading evaluations: %s", e, exc_info=True)
            raise

    def save_evaluations(self, repository: ParaphraseEvaluationRepository) -> None:
        """
        Save all paraphrase evaluations to a repository.

        :param repository: Repository implementation responsible for saving.
        """
        self.logger.info("Saving %d evaluations to repository", len(self._evaluations))
        try:
            repository.save(self._evaluations)
            self.logger.info("Evaluations saved successfully")
        except Exception as e:
            self.logger.error("Error saving evaluations: %s", e, exc_info=True)
            raise

    def load_sql_queries(self, repository: SQLRepository) -> None:
        """
        Load SQL queries from a repository.

        :param repository: Repository implementation responsible for loading.
        :raises FileNotFoundError: If the underlying data source does not exist.
        """
        try:
            self._sql_queries = repository.load()
            self.logger.info(
                "Loaded %d SQL queries successfully",
                len(self._sql_queries),
            )
        except FileNotFoundError:
            self.logger.warning("No existing SQL queries file found")
            raise
        except Exception as e:
            self.logger.error("Error loading SQL queries: %s", e, exc_info=True)
            raise

    def save_sql_queries(self, repository: SQLRepository) -> None:
        """
        Save all SQL queries to a repository.

        :param repository: Repository implementation responsible for saving.
        """
        self.logger.info("Saving %d SQL queries to repository", len(self._sql_queries))
        try:
            repository.save(self._sql_queries)
            self.logger.info("SQL queries saved successfully")
        except Exception as e:
            self.logger.error("Error saving SQL queries: %s", e, exc_info=True)
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_indices(index: int | set[int] | list[int]) -> set[int]:
        """Normalize an index specification into a set of integers."""
        if isinstance(index, int):
            return {index}
        return set(index)

    def _validate_index(self, index: int) -> None:
        """
        Validate that a question index is within bounds.

        :param index: Index to validate.
        :raises IndexError: If the index is invalid.
        """
        if index < 0 or index >= len(self._questions):
            raise IndexError("Question index out of range")

    def _get_children(
        self,
        parent: BenchmarkEntry,
        child_index: int | set[int] | None,
    ) -> list[BenchmarkEntry]:
        """Resolve child entries for a given parent."""
        if child_index is None:
            return [q for q in self._questions if q.parent_id == parent.id]

        if isinstance(child_index, set):
            for i in child_index:
                self._validate_index(i)
            return [
                self._questions[i]
                for i in child_index
                if self._questions[i].parent_id == parent.id
            ]

        self._validate_index(child_index)
        child = self._questions[child_index]
        if child.parent_id != parent.id:
            raise ValueError(
                "Specified child index does not correspond to the given parent"
            )
        return [child]

    @property
    def _paraphrase_evaluation_manager(self) -> ParaphraseEvaluationManager:
        """Lazily initialize the paraphrase evaluation manager."""
        if self._paraphrase_evaluation_manager_instance is None:
            self.logger.debug("Lazily initializing ParaphraseEvaluationManager")
            self._paraphrase_evaluation_manager_instance = (
                self._paraphrase_evaluation_manager_factory()
            )
        return self._paraphrase_evaluation_manager_instance

