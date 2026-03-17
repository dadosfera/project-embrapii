from typing import Protocol, Any, Iterable, Mapping, runtime_checkable
from contextlib import AbstractContextManager


@runtime_checkable
class DatabaseConnection(Protocol):
    """
    Base protocol for database connections.
    Repositories should depend only on this interface.
    """

    def connect(self) -> None:
        ...

    def close(self) -> None:
        ...

    def execute(
        self,
        query: str,
        params: Mapping[str, Any] | None = None
    ) -> None:
        ...

    def fetch_one(
        self,
        query: str,
        params: Mapping[str, Any] | None = None
    ) -> Mapping[str, Any] | None:
        ...

    def fetch_all(
        self,
        query: str,
        params: Mapping[str, Any] | None = None
    ) -> Iterable[Mapping[str, Any]]:
        ...

    def transaction(self) -> AbstractContextManager["DatabaseConnection"]:
        ...

    def rollback(self) -> None:
        ...

    def commit(self) -> None:
        ...