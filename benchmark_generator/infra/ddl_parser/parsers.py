import logging
from pathlib import Path

import sqlglot
import sqlglot.expressions as exp

from benchmark_generator.domain.models import Column, DatabaseSchema, ForeignKey, TableSchema
from benchmark_generator.infra.ddl_parser.protocol import DDLParser
from benchmark_generator.infra.ddl_parser.exceptions import DDLParseError

logger = logging.getLogger(__name__)

# CREATE kinds that are treated as queryable relations (tables and views).
_RELATION_KINDS = {"TABLE", "VIEW", "MATERIALIZED VIEW"}


class SQLDDLParser(DDLParser):
    """
    Converts SQL DDL (Data Definition Language) into an object-oriented database schema model.

    This parser accepts either a raw DDL string or a path to a ``.sql`` file.
    Internally, it uses ``sqlglot`` to parse the SQL and extract structural
    information such as:

    - Tables and views (regular and materialized)
    - Columns
    - Primary keys
    - Foreign keys

    Views are treated as queryable relations equivalent to tables: their column
    list is inferred from the SELECT projection of the view body.

    Only DDL statements are permitted. Non-DDL statements will raise a
    :class:`DDLParseError`.

    :param dialect: SQL dialect passed to ``sqlglot`` (e.g., ``'postgres'``,
                    ``'mysql'``, ``'sqlite'``). If ``None``, the generic
                    dialect is used.
    :type dialect: str | None

    :param database_name: Logical database name assigned to the generated
                          :class:`DatabaseSchema`.
    :type database_name: str
    """

    def __init__(
            self,
            dialect: str | None = None,
            database_name: str = "default",
    ) -> None:
        self._dialect = dialect
        self._database_name = database_name

    def parse(self, source: str | Path) -> DatabaseSchema:
        ddl = self._read_source(source)
        statements = self._parse_statements(ddl)
        tables = self._extract_tables(statements)

        if not tables:
            raise DDLParseError(
                "No CREATE TABLE or CREATE VIEW statements found in the provided DDL content."
            )

        return DatabaseSchema(
            database_name=self._database_name,
            tables=tables,
        )

    def _read_source(self, source: str | Path) -> str:
        """
        Read the DDL content from either a string or a file path.

        :param source: Either raw DDL as a string or a path to a ``.sql`` file.
        :type source: str | pathlib.Path

        :returns: The DDL content as a string.
        :rtype: str

        :raises FileNotFoundError:
            If *source* is a path that does not exist.
        """
        if isinstance(source, Path):
            if not source.exists():
                raise FileNotFoundError()
            return source.read_text(encoding="utf-8")
        return source

    def _parse_statements(self, ddl: str) -> list[exp.Expression]:
        """
        Parse DDL content and extract all SQL statements.

        Only DDL statements (CREATE, DROP, ALTER) are allowed.
        Non-DDL statements will cause a :class:`DDLParseError`.

        :param ddl: The DDL content to parse.
        :type ddl: str

        :returns: A list of parsed SQL expression objects.
        :rtype: list[sqlglot.expressions.Expression]

        :raises DDLParseError:
            If the DDL is invalid or contains non-DDL statements.
        """
        try:
            statements = sqlglot.parse(ddl, read=self._dialect, error_level=sqlglot.ErrorLevel.RAISE)
        except sqlglot.errors.SqlglotError as exc:
            raise DDLParseError(f"DDL inválido ou não reconhecido: {exc}") from exc

        if not statements or all(s is None for s in statements):
            raise DDLParseError("O conteúdo fornecido não pôde ser interpretado como SQL.")

        non_ddl = [
            s for s in statements
            if s is not None and not isinstance(s, (exp.Create, exp.Drop, exp.Alter))
        ]
        if non_ddl:
            types = {type(s).__name__ for s in non_ddl}
            raise DDLParseError(
                f"O conteúdo contém instruções que não são DDL: {', '.join(sorted(types))}."
            )

        return [s for s in statements if s is not None]

    def _extract_tables(self, statements: list[exp.Expression]) -> list[TableSchema]:
        """
        Extract all queryable relation definitions from parsed SQL statements.

        Handles ``CREATE TABLE``, ``CREATE VIEW``, and
        ``CREATE MATERIALIZED VIEW`` statements, building a :class:`TableSchema`
        for each.  Views are treated as first-class relations: their columns are
        inferred from the SELECT projection of the view body so that the
        validator can confirm query references against the schema.

        :param statements: List of parsed SQL expression objects.
        :type statements: list[sqlglot.expressions.Expression]

        :returns: A list of :class:`TableSchema` objects.
        :rtype: list[TableSchema]
        """
        tables = []
        for statement in statements:
            if not isinstance(statement, exp.Create):
                continue
            kind = (statement.kind or "").upper()
            if kind not in _RELATION_KINDS:
                continue

            logger.info("Processing %s '%s'...", kind, statement.this.sql())
            if kind == "TABLE":
                table = self._build_table_schema(statement)
            else:
                table = self._build_view_schema(statement)
            if table is not None:
                tables.append(table)
        return tables

    def _build_table_schema(self, create: exp.Create) -> TableSchema | None:
        """
        Build a :class:`TableSchema` object from a CREATE TABLE statement.

        Extracts table name, columns, primary keys, and foreign key constraints
        from the CREATE TABLE expression.

        :param create: A parsed CREATE TABLE expression.
        :type create: sqlglot.expressions.Create

        :returns: A :class:`TableSchema` instance, or ``None`` if the table
                  definition is incomplete or malformed.
        :rtype: TableSchema | None
        """
        table_expr = create.find(exp.Table)
        if table_expr is None:
            logger.warning("CREATE TABLE without identifiable name — skipped.")
            return None

        table_name = table_expr.name
        schema_def = create.find(exp.Schema)

        if schema_def is None:
            logger.warning("Table '%s' without definition body — skipped.", table_name)
            return None

        columns: list[Column] = []
        primary_keys: list[str] = []
        foreign_keys: list[ForeignKey] = []

        for definition in schema_def.find_all(exp.ColumnDef):
            column, inline_pk = self._build_column(definition)
            columns.append(column)
            if inline_pk:
                primary_keys.append(column.name)

        # for constraint in schema_def.find_all(exp.PrimaryKeyColumnConstraint):
        #     # Inline primary key already captured above via ColumnDef
        #     pass

        for constraint in schema_def.find_all(exp.PrimaryKey):
            # Table-level primary key (not inline)
            if constraint.parent and isinstance(constraint.parent, exp.ColumnDef):
                continue
            keys = [col.name for col in constraint.find_all(exp.Column)]
            if keys and not primary_keys:
                primary_keys.extend(keys)

        for fk_constraint in schema_def.find_all(exp.ForeignKey):
            fk = self._build_foreign_key(fk_constraint)
            if fk is not None:
                foreign_keys.append(fk)

        return TableSchema(
            table_name=table_name,
            columns=columns,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
        )

    def _build_view_schema(self, create: exp.Create) -> TableSchema | None:
        """
        Build a :class:`TableSchema` object from a CREATE VIEW or
        CREATE MATERIALIZED VIEW statement.

        Because views have no explicit column type declarations, columns are
        inferred from the aliases and names present in the SELECT projection of
        the view body.  Each projected expression becomes a column with data
        type ``"UNKNOWN"`` and ``is_nullable=True``.  This is sufficient for
        the validator to confirm that referenced column names exist.

        :param create: A parsed CREATE VIEW / CREATE MATERIALIZED VIEW expression.
        :type create: sqlglot.expressions.Create

        :returns: A :class:`TableSchema` instance, or ``None`` if the view
                  definition is incomplete or malformed.
        :rtype: TableSchema | None
        """
        # The view name is stored in exp.Table inside the CREATE node but
        # outside any Schema wrapper (unlike CREATE TABLE which wraps columns
        # in exp.Schema).
        table_expr = create.find(exp.Table)
        if table_expr is None:
            logger.warning("CREATE VIEW without identifiable name — skipped.")
            return None

        view_name = table_expr.name

        # The SELECT body is the expression argument of the CREATE node.
        select = create.find(exp.Select)
        if select is None:
            logger.warning("View '%s' has no SELECT body — registered with no columns.", view_name)
            return TableSchema(table_name=view_name, columns=[], primary_keys=[], foreign_keys=[])

        columns: list[Column] = []
        for projection in select.expressions:
            # Use the alias when present (AS alias), otherwise use the column
            # name for plain column references, or skip unnamed expressions.
            if projection.alias:
                col_name = projection.alias
            elif isinstance(projection, exp.Column) and projection.name:
                col_name = projection.name
            elif isinstance(projection, exp.Star):
                # SELECT * — we cannot enumerate columns statically; register
                # the view with no columns so it at least passes table-level
                # validation.
                logger.warning(
                    "View '%s' uses SELECT * — columns cannot be inferred statically.",
                    view_name,
                )
                columns = []
                break
            else:
                logger.debug(
                    "View '%s': unnamed projection '%s' skipped.", view_name, projection
                )
                continue

            columns.append(
                Column(name=col_name, data_type="UNKNOWN", is_nullable=True)
            )

        return TableSchema(
            table_name=view_name,
            columns=columns,
            primary_keys=[],
            foreign_keys=[],
        )

    def _build_column(self, col_def: exp.ColumnDef) -> tuple[Column, bool]:
        """
        Build a :class:`Column` object from a column definition.

        Extracts column name, data type, nullability, and primary key status.

        :param col_def: A parsed column definition expression.
        :type col_def: sqlglot.expressions.ColumnDef

        :returns: A tuple containing a :class:`Column` instance and a boolean
                  indicating whether this column is an inline primary key.
        :rtype: tuple[Column, bool]
        """
        name = col_def.name
        data_type = self._extract_type(col_def)
        is_nullable = self._is_nullable(col_def)
        is_primary_key = any(
            isinstance(c, exp.PrimaryKeyColumnConstraint)
            for c in col_def.find_all(exp.ColumnConstraint)
        )

        return Column(
            name=name,
            data_type=data_type,
            is_nullable=is_nullable,
        ), is_primary_key

    def _extract_type(self, col_def: exp.ColumnDef) -> str:
        """
        Extract the SQL data type from a column definition.

        :param col_def: A parsed column definition expression.
        :type col_def: sqlglot.expressions.ColumnDef

        :returns: The data type as an uppercase string, or ``"UNKNOWN"`` if
                  the data type cannot be determined.
        :rtype: str
        """
        dtype = col_def.find(exp.DataType)
        if dtype is None:
            return "UNKNOWN"
        return dtype.sql(dialect=self._dialect).upper()

    def _is_nullable(self, col_def: exp.ColumnDef) -> bool:
        """
        Determine whether a column allows NULL values.

        A column is considered NOT NULL if it has a NOT NULL constraint
        or is part of a primary key.

        :param col_def: A parsed column definition expression.
        :type col_def: sqlglot.expressions.ColumnDef

        :returns: ``True`` if the column allows NULL, ``False`` otherwise.
        :rtype: bool
        """
        for constraint in col_def.find_all(exp.ColumnConstraint):
            if isinstance(constraint.kind, exp.NotNullColumnConstraint):
                return False
            if isinstance(constraint.kind, exp.PrimaryKeyColumnConstraint):
                return False
        return True

    def _build_foreign_key(self, fk_expr: exp.ForeignKey) -> ForeignKey | None:
        """
        Build a :class:`ForeignKey` object from a foreign key constraint expression.

        Extracts the source column, referenced table, and referenced column
        from the foreign key definition.

        :param fk_expr: A parsed foreign key constraint expression.
        :type fk_expr: sqlglot.expressions.ForeignKey

        :returns: A :class:`ForeignKey` instance, or ``None`` if the constraint
                  is incomplete or malformed.
        :rtype: ForeignKey | None
        """
        source_cols = list(fk_expr.find_all(exp.Column))
        reference = fk_expr.find(exp.Reference)

        if not source_cols or reference is None:
            logger.warning("Incomplete FOREIGN KEY — ignored.")
            return None

        ref_table = reference.find(exp.Table)
        ref_cols = list(reference.find_all(exp.Column))

        if ref_table is None or not ref_cols:
            logger.warning("Incomplete FOREIGN KEY reference — ignored.")
            return None

        return ForeignKey(
            column=source_cols[0].name,
            referenced_table=ref_table.name,
            referenced_column=ref_cols[0].name,
        )


__all__ = ["SQLDDLParser"]