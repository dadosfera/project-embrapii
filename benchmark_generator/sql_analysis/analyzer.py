from typing import Protocol

from benchmark_generator.sql_analysis.parser import SQLParser
from benchmark_generator.sql_analysis.pattern_extractor import QueryPatternExtractor
from benchmark_generator.sql_analysis.table_extractor import TableExtractor


class SQLAnalyzerProtocol(Protocol):
    def analyze(
            self,
            sql: str,
            dialect: str | None = None
    ) -> tuple[list[str], list[str]]:
        """
        :returns: A tuple containing a list of table names and a list of query patterns extracted from the SQL query.
        """
        ...


class SQLAnalyzer(SQLAnalyzerProtocol):
    def __init__(
            self,
            parser: SQLParser | None = None,
            table_extractor: TableExtractor | None = None,
            pattern_extractor: QueryPatternExtractor | None = None,
    ):
        self.parser = parser or SQLParser()
        self.table_extractor = table_extractor or TableExtractor()
        self.pattern_extractor = pattern_extractor or QueryPatternExtractor()

    def analyze(
            self,
            sql: str,
            dialect: str | None = None
    ) -> tuple[list[str], list[str]]:
        tree = self.parser.parse(sql, dialect=dialect)
        tables = self.table_extractor.extract(tree)
        patterns = self.pattern_extractor.extract(tree)
        return tables, patterns

