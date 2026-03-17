from __future__ import annotations

from pathlib import Path
from typing import Protocol

from benchmark_generator.domain.models import DatabaseSchema


class DDLParser(Protocol):
    """Interface for parsing DDL statements and extracting schema information."""

    def parse(self, source: str | Path) -> "DatabaseSchema":
        """
        Parse a DDL source and construct a :class:`DatabaseSchema` instance.

        The source may be either:

        - A string containing raw DDL
        - A ``Path`` object pointing to a ``.sql`` file

        :param source: DDL string or file path.
        :type source: str | pathlib.Path

        :returns: A ```DatabaseSchema``` instance.

        :raises DDLParseError:
            If the content is invalid SQL or contains no ``CREATE TABLE`` definitions.

        :raises FileNotFoundError:
            If a ``Path`` is provided and the file does not exist.
        """
        ...

__all__ = ["DDLParser"]