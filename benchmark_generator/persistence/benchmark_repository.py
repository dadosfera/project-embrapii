import json
import logging
from json import JSONDecodeError
from pathlib import Path
from typing import Protocol, cast

from pydantic import BaseModel

from benchmark_generator import BenchmarkEntry
from benchmark_generator.domain.models import Persona, QueryPattern, QuestionDifficulty, parse_benchmark_identifier, serialize_benchmark_identifier


class BenchmarkRepository(Protocol):
    """
    Protocol for a repository that handles storage and retrieval of question batches.
    """

    def load(self) -> list[BenchmarkEntry]:
        """
        Load a batch of benchmark questions from the repository.

        :returns: A list of BenchmarkQuestion instances.
        """
        ...

    def save(self, questions: list[BenchmarkEntry]) -> None:
        """
        Save a batch of benchmark questions to the repository.

        :param questions: A list of BenchmarkQuestion instances to save.
        """
        ...

class JSONBenchmarkRepository(BenchmarkRepository):
    """
    A JSON file-based implementation of the QuestionBatchRepository protocol.
    """

    class PersonaDTO(BaseModel):
        """
        Data Transfer Object for the Persona model.
        """
        role: str
        description: str

        @classmethod
        def from_domain(cls, p: Persona) -> "JSONBenchmarkRepository.PersonaDTO":
            return cls(
                role=p.role,
                description=p.description,
            )

        def to_domain(self) -> Persona:
            return Persona(
                role=self.role,
                description=self.description,
            )

    class DTO(BaseModel):
        """
        Data Transfer Object for persisting BenchmarkEntry instances.
        """
        dataset_id: str
        question: str
        difficulty: str
        query_patterns: list[str]
        tables: list[str]

        id: str | int
        parent_id: str | int | None = None

        evidence: str | None = None
        sql: str | None = None
        persona: JSONBenchmarkRepository.PersonaDTO | None = None

        @classmethod
        def from_domain(cls, e: BenchmarkEntry) -> "JSONBenchmarkRepository.DTO":
            return cls(
                dataset_id=e.dataset_id,
                question=e.question,
                difficulty=e.difficulty,
                query_patterns=e.query_patterns,
                tables=e.tables,
                id=serialize_benchmark_identifier(e.id),
                parent_id=(
                    serialize_benchmark_identifier(e.parent_id)
                    if e.parent_id is not None else None
                ),
                evidence=e.evidence,
                sql=e.sql,
                persona=JSONBenchmarkRepository.PersonaDTO.from_domain(e.persona) if e.persona else None,
            )

        def to_domain(self) -> BenchmarkEntry:
            return BenchmarkEntry(
                dataset_id=self.dataset_id,
                question=self.question,
                difficulty=cast(QuestionDifficulty, self.difficulty),
                query_patterns=cast(list[QueryPattern], self.query_patterns),
                tables=self.tables,
                id=parse_benchmark_identifier(self.id),
                parent_id=(
                    parse_benchmark_identifier(self.parent_id)
                    if self.parent_id is not None else None
                ),
                evidence=self.evidence,
                sql=self.sql,
                persona=self.persona.to_domain() if self.persona else None,
            )


    def __init__(self, file_path: str | Path):
        """
        Initialize repository with the target JSON file path.

        :param file_path: Path to the JSON file for storing benchmark questions.
        """
        self._path = Path(file_path)
        self.logger = logging.getLogger("JSONQuestionBatchRepository")

    def load(self) -> list[BenchmarkEntry]:
        if not self._path.exists():
            self.logger.info(
                "Benchmark file does not exist, starting empty",
                extra={"path": str(self._path)},
            )
            return []

        try:
            with self._path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except JSONDecodeError:
            self.logger.warning(
                "Invalid JSON file, starting with empty dataset",
                extra={"path": str(self._path)},
            )
            return []

        return [
            self.DTO(**item).to_domain()
            for item in raw
        ]

    def save(self, questions: list[BenchmarkEntry]) -> None:
        # `model_dump` returns a dict suitable for JSON serialization (from BaseModel)
        data = [
            self.DTO.from_domain(q).model_dump(mode="json")
            for q in questions
        ]
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)