"""Extração defensiva de uma única instrução SQL da resposta de um modelo."""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp


class SqlNormalizationError(ValueError):
    """A resposta não continha exatamente uma instrução SQL parseável."""


_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)
_FENCE = re.compile(r"```(?:sql|postgresql|sqlite|mysql)?[ \t]*\r?\n?(.*?)```", re.IGNORECASE | re.DOTALL)
_PREFIX = re.compile(r"^\s*(?:sql|query|resposta)\s*:\s*", re.IGNORECASE)
_SQL_START = re.compile(r"\b(?:WITH|SELECT|INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|EXPLAIN)\b", re.IGNORECASE)


def _parse_one(text: str) -> str | None:
    """Confirma uma e somente uma instrução, sem serializar o SQL recebido."""

    candidate = _PREFIX.sub("", text.strip())
    if not candidate:
        return None
    try:
        statements = sqlglot.parse(candidate, read="postgres")
    except Exception:
        return None
    if len(statements) != 1 or statements[0] is None or isinstance(statements[0], exp.Command):
        return None
    return candidate


def _single_statement_prefix(text: str) -> str | None:
    """Aceita prosa posterior somente depois de um `;` que encerra a SQL."""

    first = _first_statement_terminator(text)
    if first < 0:
        return None
    candidate = text[: first + 1]
    remainder = text[first + 1 :].strip()
    if _SQL_START.search(remainder):
        return None
    return _parse_one(candidate)


def _first_statement_terminator(text: str) -> int:
    """Localiza `;` fora de literais e comentários, sem dividir SQL por texto."""

    quote: str | None = None
    index = 0
    while index < len(text):
        char = text[index]
        following = text[index + 1 : index + 2]
        if quote is not None:
            if char == quote:
                if following == quote:
                    index += 2
                    continue
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif char == "-" and following == "-":
            newline = text.find("\n", index + 2)
            index = len(text) if newline < 0 else newline
            continue
        elif char == "/" and following == "*":
            end = text.find("*/", index + 2)
            index = len(text) if end < 0 else end + 2
            continue
        elif char == ";":
            return index
        index += 1
    return -1


def _candidates(text: str) -> tuple[str, ...]:
    cleaned = _THINK_BLOCK.sub("", text).strip()
    sources = [cleaned]
    sources.extend(block.strip() for block in _FENCE.findall(cleaned) if block.strip())
    values: list[str] = []
    for source in sources:
        direct = _PREFIX.sub("", source.strip())
        if _PREFIX.match(source) or _SQL_START.match(source.strip()):
            values.append(direct)
        match = _SQL_START.search(source)
        if match:
            values.append(source[match.start() :].strip())
    return tuple(dict.fromkeys(values))


def normalize_sql_output(raw_output: str) -> str:
    """Extrai uma SQL única, sem jamais devolver raciocínio ou prosa do modelo."""

    if not isinstance(raw_output, str):
        raise SqlNormalizationError()
    source = raw_output.rsplit("</think>", 1)[-1] if "</think>" in raw_output else raw_output
    for candidate in _candidates(source):
        parsed = _parse_one(candidate)
        if parsed is not None:
            return parsed
        parsed = _single_statement_prefix(candidate)
        if parsed is not None:
            return parsed
        first_paragraph = re.split(r"\r?\n\s*\r?\n", candidate, maxsplit=1)[0]
        parsed = _parse_one(first_paragraph)
        if parsed is not None:
            return parsed
    raise SqlNormalizationError()
