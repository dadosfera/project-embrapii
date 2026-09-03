"""
SQL cleaning utilities for removing comments and normalizing whitespace.
"""

import re


def clean_sql(sql: str) -> str:
    """
    Cleans a SQL query by removing comments and normalizing whitespace.

    The cleaning process:
    1. Remove multi-line comments (``/* ... */``) - processed first to avoid interference
    2. Remove single-line comments (``--``)
    3. Remove all newlines
    4. Collapse multiple spaces into a single space
    5. Strip leading/trailing whitespace

    :param sql: Raw SQL query string (may contain comments and excess whitespace).
    :return: Cleaned SQL query string.

    Example:
        >>> dirty = "SELECT * FROM users -- get all users\\n  WHERE id > 0"
        >>> clean_sql(dirty)
        'SELECT * FROM users WHERE id > 0'
    """
    # Remove multi-line comments (/* ... */) FIRST
    # This prevents interference when -- appears inside /* */
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

    # Remove single-line comments (-- ...)
    sql = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)


    # Remove all newlines
    sql = sql.replace('\n', ' ')

    # Collapse multiple spaces into a single space
    sql = re.sub(r'\s+', ' ', sql)

    # Strip leading/trailing whitespace
    sql = sql.strip()

    return sql

