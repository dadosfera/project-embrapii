from __future__ import annotations

import errno
import json
import logging

import pytest

from interface.backend import diagnostics
from interface.backend.domain.errors import (
    PUBLIC_ERROR_DEFINITIONS,
    ModelLoadCause,
    PublicErrorCode,
    classify_generation_subprocess_error,
    classify_loading_model_error,
    classify_model_load_error,
    classify_query_execution_error,
    iter_exception_chain,
)


_SERIALIZED_SECRET_CASES = (
    ('{"access_token": "plainsecret"}', "plainsecret"),
    ("{'access_token': 'plainsecret'}", "plainsecret"),
    ('{"hf_token": "plainsecret"}', "plainsecret"),
    ('{"huggingface_token": "plainsecret"}', "plainsecret"),
    ('{"client_secret": "plainsecret"}', "plainsecret"),
    ('{"confirmationToken": "plainsecret"}', "plainsecret"),
    ('{"refresh_token": "plainsecret"}', "plainsecret"),
    ("access_token=plainsecret", "plainsecret"),
    ('client_secret="plain secret value"', "plain secret value"),
    ("Authorization: Bearer plainsecret", "plainsecret"),
    ('{"hfToken": "camel-hf"}', "camel-hf"),
    ('{"huggingfaceToken": "camel-huggingface"}', "camel-huggingface"),
    ('{"accessToken": "camel-access"}', "camel-access"),
    ('{"refreshToken": "camel-refresh"}', "camel-refresh"),
    ('{"authToken": "camel-auth"}', "camel-auth"),
    ('{"idToken": "camel-id"}', "camel-id"),
    ('{"oauthToken": "camel-oauth"}', "camel-oauth"),
    ('{"clientSecret": "camel-client"}', "camel-client"),
    ('{"apiKey": "camel-api"}', "camel-api"),
)


def _wrapped(root: BaseException, layers: int = 3) -> BaseException:
    current = root
    for index in range(layers):
        try:
            raise current
        except BaseException as cause:
            try:
                raise RuntimeError(f"wrapper-{index}") from cause
            except RuntimeError as wrapper:
                current = wrapper
    return current


def test_public_taxonomy_has_fallback_and_retryable_for_every_code():
    assert set(PUBLIC_ERROR_DEFINITIONS) == set(PublicErrorCode)
    assert all(item.fallback_message and isinstance(item.retryable, bool) for item in PUBLIC_ERROR_DEFINITIONS.values())


def test_direct_enospc_is_model_load_disk_full():
    classified = classify_model_load_error(OSError(errno.ENOSPC, "synthetic"))
    assert classified.cause is ModelLoadCause.DISK_FULL
    assert classified.error.code is PublicErrorCode.MODEL_LOAD_ERROR
    assert "espaço suficiente em disco" in classified.error.message
    assert classified.error.retryable is True


def test_deeply_chained_enospc_is_detected_and_chain_keeps_types():
    error = _wrapped(OSError(errno.ENOSPC, "synthetic"), layers=5)
    chain = tuple(iter_exception_chain(error))
    assert len(chain) == 6
    assert isinstance(chain[-1], OSError)
    assert classify_model_load_error(error).cause is ModelLoadCause.DISK_FULL


def test_enospc_unambiguous_text_fallback_is_detected():
    assert classify_model_load_error(RuntimeError("No space left on device")).cause is ModelLoadCause.DISK_FULL


class SyntheticCudaOutOfMemoryError(RuntimeError):
    pass


def test_cuda_oom_text_is_specific_and_not_enospc():
    classified = classify_model_load_error(RuntimeError("CUDA out of memory. Tried to allocate 2 GiB"))
    assert classified.cause is ModelLoadCause.CUDA_OOM
    assert "memória suficiente na GPU" in classified.error.message
    assert "disco" not in classified.error.message


def test_generic_cuda_error_is_not_mislabeled_as_oom():
    assert classify_model_load_error(RuntimeError("CUDA driver initialization failed")).cause is ModelLoadCause.GENERIC


def test_network_type_and_message_are_classified_conservatively():
    assert classify_model_load_error(ConnectionError("synthetic")).cause is ModelLoadCause.NETWORK
    assert classify_model_load_error(RuntimeError("Temporary failure in name resolution")).cause is ModelLoadCause.NETWORK


@pytest.mark.parametrize("message", ["Repository not found", "Access to this model is restricted"])
def test_model_unavailable_or_denied_is_separate_from_network(message):
    classified = classify_model_load_error(RuntimeError(message))
    assert classified.cause is ModelLoadCause.MODEL_UNAVAILABLE
    assert classified.error.retryable is False


def test_generic_model_load_uses_safe_fallback_and_never_reflects_secret():
    raw = "token=synthetic-secret postgresql://alice:password@db/private /srv/private/model"
    classified = classify_model_load_error(RuntimeError(raw))
    assert classified.cause is ModelLoadCause.GENERIC
    assert all(value not in classified.error.message for value in ("synthetic-secret", "alice", "/srv"))


@pytest.mark.parametrize(
    "message",
    [
        "missing result cache",
        "missing query cache",
        "incomplete chroma cache",
        "missing application cache",
    ],
)
def test_generic_cache_messages_are_not_model_unavailable(message):
    classified = classify_model_load_error(RuntimeError(message))
    assert classified.cause is ModelLoadCause.GENERIC
    assert classify_generation_subprocess_error(RuntimeError(message)).code is PublicErrorCode.SQL_GENERATION_ERROR


class PgError(RuntimeError):
    def __init__(self, sqlstate: str | None, message: str = "synthetic") -> None:
        super().__init__(message)
        self.pgcode = sqlstate


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (PgError("08006"), PublicErrorCode.DATABASE_CONNECTION_ERROR),
        (PgError("42601"), PublicErrorCode.SQL_SYNTAX_ERROR),
        (PgError("57014"), PublicErrorCode.QUERY_TIMEOUT),
        (PgError("42P01"), PublicErrorCode.QUERY_EXECUTION_ERROR),
        (RuntimeError("generic execution"), PublicErrorCode.QUERY_EXECUTION_ERROR),
    ],
)
def test_sql_errors_prefer_sqlstate_and_do_not_overclassify(error, code):
    assert classify_query_execution_error(error).code is code


def test_exception_chain_is_cycle_safe_and_bounded():
    first = RuntimeError("first")
    second = RuntimeError("second")
    first.__cause__ = second
    second.__context__ = first
    assert tuple(iter_exception_chain(first, max_depth=4)) == (first, second)


def test_exception_chain_prefers_cause_and_respects_context_suppression_and_depth():
    context_enospc = OSError(errno.ENOSPC, "No space left on device")
    context_only = RuntimeError("context only")
    context_only.__context__ = context_enospc
    context_only.__suppress_context__ = False
    assert tuple(iter_exception_chain(context_only)) == (context_only, context_enospc)
    assert classify_model_load_error(context_only).cause is ModelLoadCause.DISK_FULL

    suppressed_only = RuntimeError("suppressed only")
    suppressed_only.__context__ = context_enospc
    suppressed_only.__suppress_context__ = True
    assert tuple(iter_exception_chain(suppressed_only)) == (suppressed_only,)
    assert classify_model_load_error(suppressed_only).cause is ModelLoadCause.GENERIC

    explicit_cause = RuntimeError("explicit cause")
    outer = RuntimeError("outer")
    outer.__context__ = context_enospc
    outer.__cause__ = explicit_cause
    outer.__suppress_context__ = True

    assert tuple(iter_exception_chain(outer)) == (outer, explicit_cause)
    assert classify_model_load_error(outer).cause is ModelLoadCause.GENERIC

    deep = _wrapped(RuntimeError("root"), layers=30)
    assert len(tuple(iter_exception_chain(deep, max_depth=4))) == 4


@pytest.mark.parametrize(
    ("raw", "secret"),
    [
        ("Authorization: Bearer supersecret", "supersecret"),
        ("Authorization=Bearer supersecret", "supersecret"),
        ('{"token": "abc123"}', "abc123"),
        ("{'password': 'pw123'}", "pw123"),
        ('{"authorization": "Bearer tok123"}', "tok123"),
        ("{'authorization': 'Basic value with spaces'}", "value with spaces"),
    ],
)
def test_sanitize_message_redacts_common_quoted_and_authorization_formats(raw, secret):
    sanitized = diagnostics.sanitize_message(raw)
    assert secret not in sanitized
    assert "<redacted>" in sanitized


@pytest.mark.parametrize(("raw", "secret"), _SERIALIZED_SECRET_CASES)
def test_sanitize_message_uses_the_complete_secret_field_family(raw, secret):
    sanitized = diagnostics.sanitize_message(raw)
    assert secret not in sanitized
    assert "<redacted>" in sanitized
    if '"hf_token"' in raw:
        assert '"hf_token"' in sanitized


def test_sanitize_message_preserves_complete_non_secret_field_names():
    raw = '{"token_count": 12, "tokenizer": "qwen", "token_limit": 20, "api_key_count": 3}'
    assert diagnostics.sanitize_message(raw) == raw


@pytest.mark.parametrize(("raw", "secret"), _SERIALIZED_SECRET_CASES)
def test_serialized_secret_fields_are_safe_in_exception_traceback_and_subprocess_output(
    raw,
    secret,
    caplog,
):
    error = RuntimeError(f"exception payload: {raw}")
    error.stderr = f"stderr payload: {raw}"  # type: ignore[attr-defined]
    error.stdout = f"stdout payload: {raw}"  # type: ignore[attr-defined]

    with caplog.at_level(logging.INFO, logger="interface.runtime"):
        diagnostics.log_subprocess_failure("test.serialized-secret", error, phase="generation")

    assert secret not in diagnostics.sanitize_message(error)
    assert secret not in diagnostics.sanitize_message(f"Traceback: RuntimeError: {raw}")
    assert secret not in caplog.text
    assert "<redacted>" in caplog.text


def test_sanitizer_covers_nested_secrets_paths_traceback_and_subprocess_output(caplog):
    raw = {
        "token": "opaque-token",
        "password": "plain-password",
        "items": ["hf_abcdefghijkl", ("/srv/private/file", True, 3)],
        "postgres": "postgresql://alice:pw@db.example/base",
    }
    sanitized = diagnostics.sanitize_data(raw)
    rendered = json.dumps(sanitized)
    for value in ("opaque-token", "plain-password", "hf_abcdefghijkl", "/srv/private", "alice"):
        assert value not in rendered
    assert sanitized["items"][1][1:] == (True, 3)

    error = RuntimeError("Authorization: Bearer trace-secret\n/srv/private/trace")
    error.stderr = "Authorization=Bearer stderr-secret /srv/private/stderr"  # type: ignore[attr-defined]
    error.stdout = '{"authorization": "Bearer stdout-secret"} /srv/private/stdout'  # type: ignore[attr-defined]
    with caplog.at_level(logging.INFO, logger="interface.runtime"):
        diagnostics.log_subprocess_failure("test.subprocess", error, phase="generation")
    output = caplog.text
    for value in ("trace-secret", "stderr-secret", "stdout-secret", "/srv/private"):
        assert value not in output


def test_arbitrary_same_named_types_are_not_trusted_without_module_provenance():
    arbitrary_entry_error = type(
        "EntryNotFoundError",
        (RuntimeError,),
        {"__module__": "arbitrary.package"},
    )("missing")
    arbitrary_query_canceled = type(
        "QueryCanceledError",
        (RuntimeError,),
        {"__module__": "arbitrary.package"},
    )("canceled")

    assert classify_model_load_error(arbitrary_entry_error).cause is ModelLoadCause.GENERIC
    assert classify_generation_subprocess_error(arbitrary_entry_error).code is PublicErrorCode.SQL_GENERATION_ERROR
    assert classify_query_execution_error(arbitrary_query_canceled).code is PublicErrorCode.QUERY_EXECUTION_ERROR


def test_loading_model_generic_connection_has_no_false_database_or_download_claim():
    payload = classify_loading_model_error(ConnectionError("synthetic transport failure"))
    assert payload.code is PublicErrorCode.INTERNAL_ERROR


def test_runtime_key_is_hashed_and_numeric_boolean_types_survive(monkeypatch):
    messages: list[str] = []
    monkeypatch.setattr(diagnostics._LOGGER, "info", messages.append)
    diagnostics.log_diagnostic_event("test", key="raw-runtime-key", count=7, enabled=True)
    record = json.loads(messages[0])
    assert record["runtime_key"] != "raw-runtime-key"
    assert record["count"] == 7 and record["enabled"] is True
