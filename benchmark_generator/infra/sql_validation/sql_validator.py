"""
Main orchestrator for SQL query validation and filtering workflow.

Implements the exact flow described in the activity diagram:
  - Branch for configured DBMS vs. syntax validation
  - Iterative correction via LLM (max. ``MAX_CORRECTION_ATTEMPTS``)
  - DDL detection
  - Schema validation (tables and columns)
"""

from __future__ import annotations

import logging

import sqlglot
import sqlglot.expressions as exp

from benchmark_generator.domain.models import (
    Column,
    DatabaseSchema,
    TableSchema,
    ValidationResult,
    ValidationStatus,
)
from benchmark_generator.domain.exceptions import (
    SQLValidationError,
    SyntaxValidationError,
    LLMCorrectionError,
    SchemaValidationError,
)
from benchmark_generator.generator.sql_error_corrector import SQLErrorCorrector
from benchmark_generator.persistence.db.database_connection import DatabaseConnection

logger = logging.getLogger(__name__)

MAX_CORRECTION_ATTEMPTS = 3


class SQLValidator:
    """
    Orchestrates the complete SQL query validation and filtering workflow.

    This class implements a validation pipeline that can operate in two modes:

    1. **Database-driven mode**: Executes queries against a real DBMS to validate
       correctness and data availability.
    2. **Syntax-only mode**: Performs syntax validation without database access,
       suitable for offline validation scenarios.

    Both modes support iterative LLM-based query correction when errors are
    encountered, with configurable retry limits.

    :param schema: Optional database schema for structural validation.
                   When provided, queries are validated against defined tables
                   and columns.
    :param db_connection: Optional database connection for executing queries.
                          When provided, queries are executed against the DBMS.
                          When ``None``, only syntax validation is performed.
    :param corrector: LLM-based query corrector for automatic error fixing.
                      Defaults to a new :class:`SQLErrorCorrector` if not provided.
    :param sql_dialect: SQL dialect for parsing (e.g., ``'postgres'``, ``'mysql'``,
                        ``'sqlite'``). When ``None``, generic SQL dialect is used.
    :param documentation: Optional free-text documentation about the database,
                          forwarded to the LLM corrector for better context.
    """

    def __init__(
        self,
        schema: DatabaseSchema | None = None,
        db_connection: DatabaseConnection | None = None,
        corrector: SQLErrorCorrector | None = None,
        sql_dialect: str | None = None,
        documentation: str | None = None,
    ) -> None:
        self._schema = schema
        self._db_connection = db_connection
        self._corrector = corrector or SQLErrorCorrector()
        self._dialect = sql_dialect
        self._documentation = documentation

    # Public entry point

    def validate(self, query: str) -> ValidationResult:
        """
        Executes the complete validation flow for a given SQL query.

        Routes to :meth:`_validate_with_dbms` when a database connection is
        configured, otherwise falls back to :meth:`_validate_with_syntax`.

        :param query: Raw SQL query to validate.
        :return: Comprehensive validation result.
        """
        logger.info("Starting query validation: %.80s...", query)
        logger.debug(
            "Validation mode: %s | dialect: %s",
            "DBMS" if self._db_connection is not None else "syntax-only",
            self._dialect or "generic",
        )

        if self._db_connection is not None:
            return self._validate_with_dbms(query)
        return self._validate_with_syntax(query)

    # Branch: DBMS configured

    def _validate_with_dbms(self, query: str) -> ValidationResult:
        """
        Validates a query by executing it against a real DBMS.

        On execution failure, automatic LLM-based correction is attempted
        up to ``MAX_CORRECTION_ATTEMPTS`` times.

        :param query: SQL query to execute and validate.
        :return: Validation result indicating success or failure reason.
        """
        current_query = query
        attempts = 0

        while True:
            try:
                logger.debug(
                    "DBMS execution attempt %d/%d: %.80s...",
                    attempts + 1,
                    MAX_CORRECTION_ATTEMPTS + 1,
                    current_query,
                )
                rows = self._execute_query(current_query)
                row_count = len(rows)
                logger.info(
                    "DBMS returned %d tuple(s) from query execution (attempt %d).",
                    row_count,
                    attempts + 1,
                )

                if not rows:
                    logger.warning(
                        "Query discarded: DBMS returned 0 rows/tuples. "
                        "No data available for this query."
                    )
                    return ValidationResult(
                        original_query=query,
                        final_query=current_query,
                        status=ValidationStatus.DISCARDED_NO_ROWS,
                        message="The query returned no rows.",
                        correction_attempts=attempts,
                    )

                # The DBMS itself is the source of truth: a successful execution
                # with results is sufficient — no further schema validation needed.
                logger.info(
                    "✓ Query VALIDATED by DBMS | tuples=%d | corrections_applied=%d | final_query=%.60s...",
                    row_count,
                    attempts,
                    current_query,
                )
                return ValidationResult(
                    original_query=query,
                    final_query=current_query,
                    status=ValidationStatus.VALID,
                    message="Query is valid.",
                    correction_attempts=attempts,
                )

            except SQLValidationError as exc:
                attempts += 1
                logger.warning(
                    "Database execution error (attempt %d/%d): %s",
                    attempts,
                    MAX_CORRECTION_ATTEMPTS,
                    exc,
                )

                if attempts > MAX_CORRECTION_ATTEMPTS:
                    logger.error(
                        "Giving up after %d correction attempt(s). Final query: %.80s...",
                        attempts,
                        current_query,
                    )
                    return ValidationResult(
                        original_query=query,
                        final_query=current_query,
                        status=ValidationStatus.DISCARDED_MAX_RETRIES,
                        message=f"Maximum correction attempts reached. Last error: {exc}",
                        correction_attempts=attempts,
                    )

                try:
                    logger.debug("Requesting LLM correction (attempt %d)...", attempts)
                    current_query = self._correct_query(current_query, str(exc))
                    logger.info(
                        "Query corrected via LLM (attempt %d): %.80s...",
                        attempts,
                        current_query,
                    )
                except LLMCorrectionError as correction_exc:
                    logger.error("LLM correction failed: %s", correction_exc)
                    return ValidationResult(
                        original_query=query,
                        final_query=current_query,
                        status=ValidationStatus.DISCARDED_DB_ERROR,
                        message=f"Database error and LLM correction failed: {correction_exc}",
                        correction_attempts=attempts,
                    )

    # Branch: no DBMS — syntax validation

    def _validate_with_syntax(self, query: str) -> ValidationResult:
        """
        Validates a query using syntax analysis without DBMS access.

        On syntax errors, automatic LLM-based correction is attempted
        up to ``MAX_CORRECTION_ATTEMPTS`` times.

        :param query: SQL query to validate syntactically.
        :return: Validation result indicating success or failure reason.
        """
        current_query = query
        attempts = 0

        while attempts <= MAX_CORRECTION_ATTEMPTS:
            try:
                logger.debug(
                    "Syntax check attempt %d/%d: %.80s...",
                    attempts + 1,
                    MAX_CORRECTION_ATTEMPTS + 1,
                    current_query,
                )
                self._validate_syntax(current_query)
                logger.debug("Syntax check passed.")

                return self._check_ddl_and_schema(
                    original_query=query,
                    final_query=current_query,
                    attempts=attempts,
                )

            except SyntaxValidationError as exc:
                attempts += 1
                logger.warning(
                    "Syntax error (attempt %d/%d): %s",
                    attempts,
                    MAX_CORRECTION_ATTEMPTS,
                    exc,
                )

                if attempts > MAX_CORRECTION_ATTEMPTS:
                    logger.error(
                        "Giving up after %d correction attempt(s). Final query: %.80s...",
                        attempts,
                        current_query,
                    )
                    return ValidationResult(
                        original_query=query,
                        final_query=current_query,
                        status=ValidationStatus.DISCARDED_MAX_RETRIES,
                        message=f"Maximum correction attempts reached. Last error: {exc}",
                        correction_attempts=attempts,
                    )

                try:
                    logger.debug("Requesting LLM correction (attempt %d)...", attempts)
                    current_query = self._correct_query(current_query, str(exc))
                    logger.info(
                        "Syntax corrected via LLM (attempt %d): %.80s...",
                        attempts,
                        current_query,
                    )
                except LLMCorrectionError as correction_exc:
                    logger.error("LLM correction failed: %s", correction_exc)
                    return ValidationResult(
                        original_query=query,
                        final_query=current_query,
                        status=ValidationStatus.DISCARDED_SYNTAX_ERROR,
                        message=f"Syntax error and LLM correction failed: {correction_exc}",
                        correction_attempts=attempts,
                    )

        logger.error(
            "Exited syntax validation loop without a result after %d attempt(s).", attempts
        )
        return ValidationResult(
            original_query=query,
            final_query=current_query,
            status=ValidationStatus.DISCARDED_MAX_RETRIES,
            message="Maximum correction attempts reached.",
            correction_attempts=attempts,
        )

    # Common post-execution / post-syntax stages

    def _check_ddl_and_schema(
        self,
        original_query: str,
        final_query: str,
        attempts: int,
    ) -> ValidationResult:
        """
        Checks for DDL statements and validates against schema when available.

        Flow:
        1. If the query contains DDL → discard.
        2. If a :class:`DatabaseSchema` is configured → extract tables and
           columns from the query and verify they all exist in the schema.
           Discard on mismatch, accept otherwise.
        3. If no schema is configured → accept directly.

        :param original_query: Original query before corrections.
        :param final_query: Query after potential corrections.
        :param attempts: Number of correction attempts performed.
        :return: Validation result.
        """
        if self._contains_ddl(final_query):
            logger.info("Query discarded: contains DDL.")
            return ValidationResult(
                original_query=original_query,
                final_query=final_query,
                status=ValidationStatus.DISCARDED_DDL_FOUND,
                message="The query contains DDL statements (CREATE/DROP/ALTER/etc.).",
                correction_attempts=attempts,
            )

        logger.debug("DDL check passed — no DDL statements found.")
        return self._validate_schema_and_build_result(
            original_query=original_query,
            final_query=final_query,
            attempts=attempts,
        )

    def _validate_schema_and_build_result(
        self,
        original_query: str,
        final_query: str,
        attempts: int,
    ) -> ValidationResult:
        """
        Extracts tables/columns from the query and validates them against the
        configured :class:`DatabaseSchema` (when present).

        :param original_query: Original query before corrections.
        :param final_query: Query after potential corrections.
        :param attempts: Number of correction attempts performed.
        :return: Validation result with extracted metadata.
        """
        tables, columns = self._extract_tables_and_columns(final_query)
        logger.debug(
            "Extracted tables=%s | columns=%s",
            tables,
            columns,
        )

        if self._schema is not None:
            logger.debug(
                "Validating against schema '%s' (%d table(s)).",
                self._schema.database_name,
                len(self._schema.tables),
            )
            try:
                self._validate_against_schema(tables, columns)
                logger.debug("Schema validation passed.")
            except SchemaValidationError as exc:
                logger.info("Query discarded: schema mismatch. %s", exc)
                return ValidationResult(
                    original_query=original_query,
                    final_query=final_query,
                    status=ValidationStatus.DISCARDED_SCHEMA_MISMATCH,
                    message=str(exc),
                    tables_used=tables,
                    columns_used=columns,
                    correction_attempts=attempts,
                )
        else:
            logger.debug("No schema configured — skipping schema validation.")

        logger.info(
            "Query successfully validated (tables=%s, %d correction(s) applied).",
            tables,
            attempts,
        )
        return ValidationResult(
            original_query=original_query,
            final_query=final_query,
            status=ValidationStatus.VALID,
            message="Query is valid.",
            tables_used=tables,
            columns_used=columns,
            correction_attempts=attempts,
        )

    # Low-level helpers

    def _validate_syntax(self, query: str) -> None:
        """
        Parses the query with ``sqlglot`` to verify syntactic correctness.

        :param query: SQL query string.
        :raises SyntaxValidationError: If the query cannot be parsed.
        """
        logger.debug("Running sqlglot parse (dialect=%s).", self._dialect or "generic")
        try:
            sqlglot.parse_one(query, read=self._dialect, error_level=sqlglot.ErrorLevel.RAISE)
        except sqlglot.errors.SqlglotError as exc:
            logger.debug("sqlglot parse failed: %s", exc)
            raise SyntaxValidationError(str(exc)) from exc

    def _contains_ddl(self, query: str) -> bool:
        """
        Checks whether the query string contains any DDL statements.

        :param query: SQL query string.
        :return: ``True`` if at least one DDL statement is found.
        """
        try:
            statements = sqlglot.parse(query, read=self._dialect)
        except sqlglot.errors.SqlglotError:
            return False

        return any(
            isinstance(stmt, (exp.Create, exp.Drop, exp.Alter))
            for stmt in statements
            if stmt is not None
        )

    def _extract_tables_and_columns(self, query: str) -> tuple[list[str], list[str]]:
        """
        Extracts all table and column references from a SQL query.

        Only columns that are genuine schema references are returned.
        Computed aliases introduced by ``AS`` in the SELECT list (e.g.
        ``COUNT(*) AS total``) are excluded so that schema validation never
        rejects dynamically named output columns.

        :param query: SQL query string.
        :return: A ``(tables, columns)`` tuple with sorted, deduplicated names.
        """
        try:
            tree = sqlglot.parse_one(query, read=self._dialect)
        except sqlglot.errors.SqlglotError:
            return [], []

        tables: set[str] = set()
        columns: set[str] = set()

        # Collect CTE names so they are not validated against the schema.
        cte_names: set[str] = {
            cte.alias.lower()
            for cte in tree.find_all(exp.CTE)
            if cte.alias
        }

        for table_node in tree.find_all(exp.Table):
            if table_node.name and table_node.name.lower() not in cte_names:
                tables.add(table_node.name)

        # Collect aliases defined in SELECT projections so they are excluded
        # from schema validation (they are computed names, not schema columns).
        select_aliases: set[str] = set()
        for select in tree.find_all(exp.Select):
            for projection in select.expressions:
                if isinstance(projection, exp.Alias) and projection.alias:
                    select_aliases.add(projection.alias.lower())

        for col_node in tree.find_all(exp.Column):
            name = col_node.name
            if name and name.lower() not in select_aliases:
                columns.add(name)

        return sorted(tables), sorted(columns)

    def _validate_against_schema(
        self,
        query_tables: list[str],
        query_columns: list[str],
    ) -> None:
        """
        Validates that all referenced tables and columns exist in the
        configured :class:`DatabaseSchema`.

        :param query_tables: Table names extracted from the query.
        :param query_columns: Column names extracted from the query.
        :raises SchemaValidationError:
            If any table or column is not found in the schema.
        """
        if self._schema is None:
            return

        schema_table_list: list[TableSchema] = self._schema.tables
        schema_tables = {tbl.table_name.lower() for tbl in schema_table_list}

        all_columns: list[Column] = [
            col for tbl in schema_table_list for col in tbl.columns
        ]
        schema_columns = {col.name.lower() for col in all_columns}

        unknown_tables = {t for t in query_tables if t.lower() not in schema_tables}
        if unknown_tables:
            raise SchemaValidationError(
                f"Tables not found in schema: {', '.join(sorted(unknown_tables))}."
            )

        unknown_columns = {c for c in query_columns if c.lower() not in schema_columns}
        if unknown_columns:
            raise SchemaValidationError(
                f"Columns not found in schema: {', '.join(sorted(unknown_columns))}."
            )

    def _execute_query(self, query: str) -> list:
        """
        Executes a query against the configured database connection.

        Logs the number of tuples (rows) returned from the DBMS.

        :param query: SQL query string.
        :return: List of result rows (tuples).
        :raises SQLValidationError: If execution fails.
        """
        if self._db_connection is None:
            raise SQLValidationError("No database connection configured.")
        self._db_connection.rollback()

        try:
            logger.debug("Executing query against DBMS: %.80s...", query)
            rows = list(self._db_connection.fetch_all(query))
            row_count = len(rows)
            logger.debug(
                "DBMS fetch completed — fetched %d tuple(s) | first_row_preview=%s",
                row_count,
                str(rows[0])[:100] if rows else "(empty result set)",
            )
            return rows
        except Exception as exc:
            logger.warning("DBMS fetch failed with exception: %s", exc)
            self._db_connection.rollback()
            raise SQLValidationError(str(exc)) from exc

    def _correct_query(self, query: str, error_message: str) -> str:
        """
        Delegates query correction to the LLM-based
        :class:`~benchmark_generator.generator.sql_error_corrector.SQLErrorCorrector`.

        :param query: The failed SQL query.
        :param error_message: The error message from parsing or execution.
        :return: The corrected SQL query string.
        :raises LLMCorrectionError: If the LLM correction itself fails.
        """
        try:
            schema_str = str(self._schema) if self._schema else None
            logger.debug(
                "Calling LLM corrector | has_schema=%s | has_docs=%s | dialect=%s",
                schema_str is not None,
                self._documentation is not None,
                self._dialect or "generic",
            )
            corrected = self._corrector.generate(
                generated_sql=query,
                error_message=error_message,
                schema=schema_str,
                documentation=self._documentation,
                sql_dialect=self._dialect,
            )
            logger.debug("LLM corrector returned: %.80s...", corrected)
            return corrected
        except Exception as exc:
            raise LLMCorrectionError(str(exc)) from exc


