import json
import logging
from pathlib import Path
from typing import Protocol
from json import JSONDecodeError

from pydantic import BaseModel
from typing import Protocol

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