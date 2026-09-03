"""Registro interno, estruturado e seguro do ciclo de vida de runtimes."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import traceback
from typing import Any


_LOGGER = logging.getLogger("interface.runtime")
_SECRET_FIELD_NAME_PATTERN = (
    r"(?:token|"
    r"(?:hf|huggingface|access|refresh|auth|id|oauth|confirmation)[_-]?token|"
    r"password|passwd|secret|client[_-]?secret|api[_-]?key|authorization)"
)
_QUOTED_SECRET_VALUE = re.compile(
    r"(?i)(?P<prefix>(?P<key_quote>['\"])?"
    rf"{_SECRET_FIELD_NAME_PATTERN}"
    r"(?(key_quote)(?P=key_quote))\s*[:=]\s*)"
    r"(?P<value_quote>['\"])(?:\\.|(?!(?P=value_quote)).)*(?P=value_quote)"
)
_UNQUOTED_AUTHORIZATION = re.compile(
    r"(?i)(?P<prefix>(?P<key_quote>['\"])?authorization"
    r"(?(key_quote)(?P=key_quote))\s*[:=]\s*)"
    r"(?:[A-Za-z][A-Za-z0-9._-]*\s+)?[^\s,;}\]]+"
)
_UNQUOTED_SECRET_VALUE = re.compile(
    r"(?i)(?P<prefix>(?P<key_quote>['\"])?"
    rf"{_SECRET_FIELD_NAME_PATTERN}"
    r"(?(key_quote)(?P=key_quote))\s*[:=]\s*)[^\s,;}\]]+"
)
_QUERY_SECRET = re.compile(
    r"(?i)([?&](?:token|signature|credential|x-amz-signature)=)[^&\s]+"
)
_HF_TOKEN = re.compile(
    r"(?i)\bhf_(?![A-Za-z0-9_-]+['\"]?\s*[:=])[A-Za-z0-9_-]+"
)
_POSTGRES_CREDENTIALS = re.compile(r"(?i)(postgres(?:ql)?://)[^\s@]+@")
_ABSOLUTE_PATH = re.compile(r"(?<![\w.-])/(?:[^\s:'\"\\]+/?)+")
_WINDOWS_ABSOLUTE_PATH = re.compile(r"(?i)(?<![\w.-])[a-z]:\\(?:[^\s:'\"\\]+\\?)+")
_SECRET_FIELD = re.compile(rf"(?i)^{_SECRET_FIELD_NAME_PATTERN}$")


def sanitize_message(value: object, *, limit: int = 800) -> str:
    """Remove segredos, URLs com credenciais e caminhos locais de diagnósticos."""

    message = str(value).replace("\r", " ")
    message = _QUOTED_SECRET_VALUE.sub(r"\g<prefix><redacted>", message)
    message = _UNQUOTED_AUTHORIZATION.sub(r"\g<prefix><redacted>", message)
    message = _UNQUOTED_SECRET_VALUE.sub(r"\g<prefix><redacted>", message)
    message = _QUERY_SECRET.sub(r"\1<redacted>", message)
    message = _HF_TOKEN.sub("<redacted>", message)
    message = _POSTGRES_CREDENTIALS.sub(r"\1<redacted>@", message)
    message = _ABSOLUTE_PATH.sub("<path>", message)
    message = _WINDOWS_ABSOLUTE_PATH.sub("<path>", message)
    return message.replace("\n", " ")[:limit]


def _safe_value(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def sanitize_data(value: object) -> object:
    """Sanitiza campos estruturados sem perder números ou sua estrutura."""

    if isinstance(value, str):
        return sanitize_message(value)
    if isinstance(value, list):
        return [sanitize_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_data(item) for item in value)
    if isinstance(value, dict):
        sanitized: dict[object, object] = {}
        for key, item in value.items():
            secret_field = isinstance(key, str) and _SECRET_FIELD.fullmatch(key) is not None
            safe_key = (
                key
                if secret_field
                else sanitize_message(key)
                if isinstance(key, str)
                else key
            )
            sanitized[safe_key] = (
                "<redacted>"
                if secret_field
                else sanitize_data(item)
            )
        return sanitized
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return sanitize_message(value)


# Compatibilidade interna com o nome usado nas fases anteriores.
_sanitize_field = sanitize_data


def log_diagnostic_event(
    event: str,
    *,
    exception: BaseException | None = None,
    key: object | None = None,
    **fields: object,
) -> None:
    """Emite um diagnóstico estruturado, sanitizado e limitado."""

    record: dict[str, Any] = {"event": sanitize_message(event, limit=160)}
    if key is not None:
        record["runtime_key"] = _safe_value(key)
    sanitized_fields = sanitize_data(fields)
    assert isinstance(sanitized_fields, dict)
    for name, value in sanitized_fields.items():
        if value is not None:
            record[name] = value
    if exception is not None:
        record["exception_type"] = type(exception).__name__
        record["exception_message"] = sanitize_message(exception)
    _LOGGER.info(json.dumps(record, ensure_ascii=False, sort_keys=True))
    if exception is not None:
        trace = sanitize_message(
            "".join(traceback.format_exception(exception)),
            limit=4_000,
        )
        _LOGGER.error("diagnostic.traceback %s", trace)


def log_runtime_event(event: str, *, stage: str | None = None, exception: BaseException | None = None, key: object | None = None, **fields: object) -> None:
    """Emite JSON para o log local, sem propagar detalhes a HTTP."""

    log_diagnostic_event(
        event,
        stage=stage,
        exception=exception,
        key=key,
        **fields,
    )


def log_subprocess_failure(
    event: str,
    exception: BaseException,
    *,
    phase: str,
) -> None:
    """Registra somente amostras sanitizadas; nunca persiste output integral."""

    fields: dict[str, object] = {
        "phase": phase,
        "return_code": getattr(exception, "returncode", None),
    }
    for name in ("stdout", "stderr", "output"):
        value = getattr(exception, name, None)
        if value:
            fields[name] = sanitize_message(value, limit=2_000)
    log_diagnostic_event(event, exception=exception, **fields)


def shared_system_cache_snapshot() -> tuple[int | None, tuple[str, ...]]:
    """Lê somente metadados do cache Chroma quando a versão os expõe."""

    try:
        from chromadb.api.client import SharedSystemClient

        systems = getattr(SharedSystemClient, "_identifer_to_system", None)
        if not isinstance(systems, dict):
            return None, ()
        return len(systems), tuple(sorted(_safe_value(identifier) for identifier in systems))
    except Exception:
        return None, ()
