import json
import logging
from json import JSONDecodeError
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from benchmark_generator.domain.models import DetailedSQL


class SQLRepository(Protocol):
    """
    Protocol for repositories that store and retrieve DetailedSQL entries.
    """

    def load(self) -> list[DetailedSQL]:
        """
        Load a collection of detailed SQL entries.

        :return: A list of DetailedSQL objects.
        """
        ...

    def save(self, sqls: list[DetailedSQL]) -> None:
        """
        Persist a collection of detailed SQL entries.

        :param sqls: A list of DetailedSQL objects to persist.
        """
        ...


class JSONSQLRepository(SQLRepository):
    """
    JSON file-based implementation of SQLRepository.
    """

    class DTO(BaseModel):
        """
        Data Transfer Object for persisting DetailedSQL instances.
        """
        sql: str
        dialect: str
        description: str
        difficulty: str
        tables: list[str]
        query_patterns: list[str]

        @classmethod
        def from_domain(cls, e: DetailedSQL) -> "JSONSQLRepository.DTO":
            return cls(
                sql=e.sql,
                dialect=e.dialect,
                description=e.description,
                difficulty=e.difficulty,
                tables=e.tables,
                query_patterns=e.query_patterns,
            )

        def to_domain(self) -> DetailedSQL:
            return DetailedSQL(
                sql=self.sql,
                dialect=self.dialect,
                description=self.description,
                difficulty=self.difficulty,
                tables=self.tables,
                query_patterns=self.query_patterns,
            )

    def __init__(self, file_path: str | Path):
        """
        Initialize repository with the target JSON file path.

        :param file_path: Path to the JSON file for storing SQL entries.
        """
        self._path = Path(file_path)
        self.logger = logging.getLogger("JSONSQLRepository")

    def load(self) -> list[DetailedSQL]:
        if not self._path.exists():
            self.logger.info(
                "SQL repository file does not exist, starting empty",
                extra={"path": str(self._path)},
            )
            return []

        try:
            with self._path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except JSONDecodeError:
            self.logger.warning(
                "Invalid JSON file, starting with empty SQL repository",
                extra={"path": str(self._path)},
            )
            return []

        return [
            self.DTO(**item).to_domain()
            for item in raw
        ]

    def save(self, sqls: list[DetailedSQL]) -> None:
        data = [
            self.DTO.from_domain(sql).model_dump(mode="json")
            for sql in sqls
        ]

        with self._path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)