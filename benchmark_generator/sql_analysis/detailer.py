from typing import Protocol

from benchmark_generator.domain.models import InitialSQL, DetailedSQL
from benchmark_generator.sql_analysis.analyzer import SQLAnalyzer


class SQLDetailerProtocol(Protocol):
    def detail(self, initial_sql: InitialSQL) -> DetailedSQL:
        ...


class SQLDetailer(SQLDetailerProtocol):
    def __init__(
            self,
            analyzer: SQLAnalyzer = SQLAnalyzer()
    ):
        self.analyzer = analyzer

    def detail(self, entry: InitialSQL) -> DetailedSQL:
        tables, patterns = self.analyzer.analyze(
            entry.sql,
            dialect=entry.dialect
        )

        return DetailedSQL(
            sql=entry.sql,
            dialect=entry.dialect,
            description=entry.description,
            difficulty=entry.difficulty,
            tables=tables,
            query_patterns=patterns,
        )
