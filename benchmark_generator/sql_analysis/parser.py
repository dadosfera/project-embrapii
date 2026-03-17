import sqlglot
from sqlglot import exp


class SQLParser:
    def parse(self, sql: str, dialect: str | None = None) -> exp.Expression:
        """
        Parses the given SQL query and returns its abstract syntax tree (AST).
        """
        return sqlglot.parse_one(sql, read="postgres" if dialect == "postgresql" else dialect)