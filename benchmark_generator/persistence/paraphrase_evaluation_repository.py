import json
import logging
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel
from benchmark_generator.domain.models import (
    ParaphraseEvaluation,
    parse_benchmark_identifier,
    serialize_benchmark_identifier,
)


class ParaphraseEvaluationRepository(Protocol):
    def load(self) -> list[ParaphraseEvaluation]:
        ...

    def save(self, evaluations: list[ParaphraseEvaluation]) -> None:
        ...


class JSONParaphraseEvaluationRepository:
    """
    JSON-based repository for storing paraphrase evaluation results.
    """

    class DTO(BaseModel):
        parent_id: str | int
        child_id: str | int
        method: str
        score: float
        parent_question: str | None = None
        child_question: str | None = None
        details: dict | None = None

        @classmethod
        def from_domain(cls, e: ParaphraseEvaluation):
            return cls(
                parent_id=serialize_benchmark_identifier(e.parent_id),
                child_id=serialize_benchmark_identifier(e.child_id),
                method=e.method,
                score=e.score,
                parent_question=e.parent_question,
                child_question=e.child_question,
                details=e.details,
            )

        def to_domain(self) -> ParaphraseEvaluation:
            return ParaphraseEvaluation(
                parent_id=parse_benchmark_identifier(self.parent_id),
                child_id=parse_benchmark_identifier(self.child_id),
                method=self.method,
                score=self.score,
                parent_question=self.parent_question,
                child_question=self.child_question,
                details=self.details,
            )

    def __init__(self, file_path: str | Path):
        self._path = Path(file_path)
        self.logger = logging.getLogger("JSONParaphraseEvaluationRepository")

    def load(self) -> list[ParaphraseEvaluation]:
        if not self._path.exists():
            self.logger.info("Evaluation file not found, starting empty")
            return []

        with self._path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        return [self.DTO(**item).to_domain() for item in raw]

    def save(self, evaluations: list[ParaphraseEvaluation]) -> None:
        data = [self.DTO.from_domain(e).model_dump() for e in evaluations]
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)