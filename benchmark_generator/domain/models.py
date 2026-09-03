import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Optional, TypeAlias
from uuid import UUID, uuid4

BenchmarkIdentifier: TypeAlias = UUID | int
SerializedBenchmarkIdentifier: TypeAlias = str | int


def parse_benchmark_identifier(value: BenchmarkIdentifier | SerializedBenchmarkIdentifier) -> BenchmarkIdentifier:
    """Parse a benchmark identifier preserving integers and converting UUID strings."""
    if isinstance(value, UUID | int):
        return value
    return UUID(value)


def serialize_benchmark_identifier(value: BenchmarkIdentifier) -> SerializedBenchmarkIdentifier:
    """Serialize a benchmark identifier preserving ints and storing UUIDs as strings."""
    if isinstance(value, int):
        return value
    return str(value)

QueryPattern = Literal[
    "select",
    "filter",
    "aggregation",
    "join",
    "subquery",
    "ordering",
    "set",
    "dialect_function",
]

QuestionDifficulty = Literal["simple", "medium", "hard"]

@dataclass
class Persona:
    role: str
    description: str


@dataclass
class BenchmarkEntry:
    dataset_id: str
    question: str
    difficulty: QuestionDifficulty
    query_patterns: list[QueryPattern]
    tables: list[str]

    id: BenchmarkIdentifier = field(default_factory=uuid4)

    evidence: str | None = None
    sql: str | None = None
    persona: Persona | None = None

    # Provenence
    parent_id: BenchmarkIdentifier | None = None


@dataclass
class Benchmark:
    items: list[BenchmarkEntry]


@dataclass
class Dataset:
    """
    Represents a dataset used as the basis for benchmark generation.

    The :attr:`schema` field must contain a valid SQL DDL string.
    The :attr:`database_schema` property lazily parses it into a
    :class:`DatabaseSchema` on first access, caching the result for
    subsequent calls. If parsing fails, the error is stored and
    re-raised on every access while the cache remains ``None``.

    :ivar id: Unique identifier for this dataset.
    :ivar schema: Raw SQL DDL string describing the database structure.
    :ivar documentation: Optional human-readable documentation about the dataset.
    """

    id: str
    schema: str
    documentation: str | None = None

    # private cache — not part of the public interface
    _database_schema: "DatabaseSchema | None" = field(default=None, init=False, repr=False, compare=False)
    _database_schema_error: "Exception | None" = field(default=None, init=False, repr=False, compare=False)

    def parse_schema(self) -> "DatabaseSchema":
        """
        Parses :attr:`schema` as SQL DDL and returns a :class:`DatabaseSchema`.

        This method always performs a fresh parse without touching the cache.
        Prefer :attr:`database_schema` for cached access.

        :returns: The parsed database schema.
        :rtype: DatabaseSchema

        :raises DDLParseError:
            If :attr:`schema` is not valid SQL DDL or contains no
            ``CREATE TABLE`` definitions.
        """
        from benchmark_generator.infra.ddl_parser import SQLDDLParser

        parser = SQLDDLParser(database_name=self.id)
        return parser.parse(self.schema)

    @property
    def database_schema(self) -> "DatabaseSchema":
        """
        Lazily parsed :class:`DatabaseSchema` derived from :attr:`schema`.

        The result is computed once and cached in ``_database_schema``.
        If parsing raises a :class:`~benchmark_generator.infra.ddl_parser.DDLParseError`,
        the error is stored in ``_database_schema_error`` and re-raised on
        every subsequent access; ``_database_schema`` remains ``None``.

        :returns: The cached or freshly parsed database schema.
        :rtype: DatabaseSchema

        :raises DDLParseError:
            If :attr:`schema` is not valid SQL DDL. The exception is cached
            and re-raised on every access until the object is mutated.
        """
        if self._database_schema_error is not None:
            raise self._database_schema_error

        if self._database_schema is None:
            try:
                object.__setattr__(self, "_database_schema", self.parse_schema())
            except Exception as exc:
                object.__setattr__(self, "_database_schema_error", exc)
                raise

        return self._database_schema


@dataclass
class ParaphraseEvaluation:
    """
    Represents the evaluation result between a parent question
    and a paraphrased (child) question.
    """
    parent_id: BenchmarkIdentifier
    child_id: BenchmarkIdentifier

    method: str
    score: float

    # Optional denormalized text
    parent_question: str | None = None
    child_question: str | None = None

    # Extra method-specific outputs
    details: dict[str, float] | None = None


###

@dataclass
class InitialSQL:
    sql: str
    dialect: str
    description: str
    difficulty: QuestionDifficulty

@dataclass
class DetailedSQL:
    sql: str
    dialect: str
    description: str
    difficulty: QuestionDifficulty
    tables: list[str]
    query_patterns: list[QueryPattern]


###

@dataclass
class Column:
    """Representa uma coluna no banco de dados."""
    name: str
    data_type: str
    description: str | None = None
    is_nullable: bool = True


@dataclass
class ForeignKey:
    """Representa uma chave estrangeira."""
    column: str
    referenced_table: str
    referenced_column: str


@dataclass
class TableSchema:
    """Representa o schema de uma tabela."""
    table_name: str
    columns: list[Column]
    primary_keys: list[str]
    foreign_keys: list[ForeignKey] = field(default_factory=list)
    description: str | None = None

    def to_dict(self):
        """Converte para dicionário."""
        return {
            "table_name": self.table_name,
            "description": self.description,
            "columns": [
                {
                    "name": col.name,
                    "type": col.data_type,
                    "description": col.description,
                    "nullable": col.is_nullable
                }
                for col in self.columns
            ],
            "primary_keys": self.primary_keys,
            "foreign_keys": [
                {
                    "column": fk.column,
                    "references": f"{fk.referenced_table}.{fk.referenced_column}"
                }
                for fk in self.foreign_keys
            ]
        }

    def to_sql(self) -> str:
        """Converte o esquema da tabela para SQL DDL (CREATE TABLE)."""
        lines = []

        if self.description:
            lines.append(f"-- {self.description}")
        lines.append(f"CREATE TABLE IF NOT EXISTS {self.table_name} (")

        # vamos construir uma lista de "definições" sem vírgulas finais
        defs = []

        # Definições das colunas (sem vírgula)
        for col in self.columns:
            base = f"  {col.name} {col.data_type}"
            if not col.is_nullable:
                base += " NOT NULL"
            # guardamos a descrição separada para controlar a posição da vírgula
            comment = f" -- {col.description}" if col.description else ""
            defs.append((base, comment))

        # Chaves primárias
        if self.primary_keys:
            pk_base = f"  PRIMARY KEY ({', '.join(self.primary_keys)})"
            defs.append((pk_base, ""))

        # Chaves estrangeiras
        for fk in self.foreign_keys:
            fk_base = f"  FOREIGN KEY ({fk.column}) REFERENCES {fk.referenced_table}({fk.referenced_column})"
            defs.append((fk_base, ""))

        # Agora montamos as linhas colocando a vírgula **antes** do comentário (quando houver)
        table_lines = []
        for i, (base, comment) in enumerate(defs):
            is_last = (i == len(defs) - 1)
            if comment:
                # vírgula vem antes do comentário
                line = base + ("," if not is_last else "") + comment
            else:
                # sem comentário: vírgula no fim (se não for o último)
                line = base + ("," if not is_last else "")
            table_lines.append(line)

        # adiciona o corpo e fecha
        lines.extend(table_lines)
        lines.append(");")

        return "\n".join(lines)


@dataclass
class DatabaseSchema:
    """Representa o schema completo do banco de dados."""
    database_name: str
    tables: list[TableSchema]
    description: Optional[str] = None

    def __str__(self):
        return self.to_formatted_string()

    def to_formatted_string(self) -> str:
        """Converte o schema para uma string formatada legível."""
        lines = [f"Database: {self.database_name}"]
        if self.description:
            lines.append(f"Description: {self.description}")
        lines.append("")

        for table in self.tables:
            lines.append(f"Table: {table.table_name}")
            if table.description:
                lines.append(f"  Description: {table.description}")

            lines.append("  Columns:")
            for col in table.columns:
                col_info = f"    - {col.name} ({col.data_type})"
                if col.description:
                    col_info += f" - {col.description}"
                if not col.is_nullable:
                    col_info += " [NOT NULL]"
                lines.append(col_info)

            if table.primary_keys:
                lines.append(f"  Primary Keys: {', '.join(table.primary_keys)}")

            if table.foreign_keys:
                lines.append("  Foreign Keys:")
                for fk in table.foreign_keys:
                    lines.append(f"    - {fk.column} -> {fk.referenced_table}.{fk.referenced_column}")

            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Converte para JSON."""
        return json.dumps({
            "database_name": self.database_name,
            "description": self.description,
            "tables": [table.to_dict() for table in self.tables]
        }, indent=2)

    def to_sql(self) -> str:
        """Converte o schema completo para SQL DDL."""
        lines = []
        lines.append(f"-- Database: {self.database_name}\n")
        if self.description: lines.append(f"-- {self.description}")

        table_schemas = [table.to_sql() for table in self.tables]
        lines.append('\n\n'.join(table_schemas))
        return "\n".join(lines)

class ValidationStatus(str, Enum):
    """
    Enumeration of possible SQL query validation outcomes.

    :cvar VALID: Query passed all validation checks and is ready for use.
    :cvar DISCARDED_NO_ROWS: Query executed successfully but returned no rows.
    :cvar DISCARDED_MAX_RETRIES: Query validation failed after exceeding maximum correction attempts.
    :cvar DISCARDED_DB_ERROR: Query execution failed in the database with LLM correction also failing.
    :cvar DISCARDED_SYNTAX_ERROR: Query has syntax errors and LLM correction failed.
    :cvar DISCARDED_DDL_FOUND: Query contains DDL statements (CREATE/DROP/ALTER).
    :cvar DISCARDED_SCHEMA_MISMATCH: Query references tables or columns not in the provided schema.
    """
    VALID = "valid"
    DISCARDED_NO_ROWS = "discarded_no_rows"
    DISCARDED_MAX_RETRIES = "discarded_max_retries"
    DISCARDED_DB_ERROR = "discarded_db_error"
    DISCARDED_SYNTAX_ERROR = "discarded_syntax_error"
    DISCARDED_DDL_FOUND = "discarded_ddl_found"
    DISCARDED_SCHEMA_MISMATCH = "discarded_schema_mismatch"


@dataclass
class ValidationResult:
    """
    Encapsulates the complete result of SQL query validation and filtering.

    This data structure captures all relevant information about a query's
    validation journey, including its original form, final corrected form,
    validation status, and metadata about the validation process.

    :ivar original_query: The SQL query as originally provided before any corrections.
    :ivar final_query: The SQL query after potential LLM-based corrections.
    :ivar status: The validation outcome status indicating acceptance or rejection reason.
    :ivar message: Human-readable description of the validation result.
    :ivar correction_attempts: Number of LLM correction attempts performed (0 if none).
    :ivar tables_used: List of table names referenced in the validated query.
                       Available only after schema extraction succeeds.
    :ivar columns_used: List of fully qualified column names (table.column format)
                        referenced in the validated query.
                        Available only after schema extraction succeeds.
    """
    original_query: str
    final_query: str
    status: ValidationStatus
    message: str
    correction_attempts: int
    tables_used: list[str] | None = None
    columns_used: list[str] | None = None

    @property
    def is_valid(self) -> bool:
        """
        Convenience property to check if validation was successful.

        :return: True if status is VALID, False otherwise.
        """
        return self.status == ValidationStatus.VALID

    @property
    def was_corrected(self) -> bool:
        """
        Indicates whether the query was modified by LLM corrections.

        :return: True if original_query differs from final_query, False otherwise.
        """
        return self.original_query != self.final_query

    def to_dict(self) -> dict:
        """
        Converts the validation result to a dictionary representation.

        :return: Dictionary containing all validation result attributes.
        """
        return {
            "original_query": self.original_query,
            "final_query": self.final_query,
            "status": self.status.value,
            "message": self.message,
            "correction_attempts": self.correction_attempts,
            "tables_used": self.tables_used or [],
            "columns_used": self.columns_used or [],
            "is_valid": self.is_valid,
            "was_corrected": self.was_corrected,
        }
