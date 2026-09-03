
class SQLValidationError(Exception):
    """Raised when a SQL query fails execution against a DBMS."""


class SyntaxValidationError(Exception):
    """Raised when a SQL query has syntax errors."""


class LLMCorrectionError(Exception):
    """Raised when the LLM-based correction fails."""


class SchemaValidationError(Exception):
    """Raised when a query references tables or columns outside the schema."""