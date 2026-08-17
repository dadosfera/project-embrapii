from __future__ import annotations

import json

from interface.backend import diagnostics


def _record(monkeypatch, **fields):
    messages: list[str] = []
    monkeypatch.setattr(diagnostics._LOGGER, "info", messages.append)
    diagnostics.log_runtime_event("test.event", key="raw-runtime-key", **fields)
    return json.loads(messages[0])


def test_diagnostics_sanitizes_nested_field_values_and_preserves_scalars(monkeypatch):
    record = _record(
        monkeypatch,
        token="token=abc",
        password="password=abc",
        hf="hf_xxxxx",
        postgres="postgresql://alice:password@db.example/test",
        path="/private/runtime/workspace",
        nested={"secret": "secret=inside", "count": 7},
        values=["api_key=listed", ("/private/list-path", True, 2.5)],
        enabled=True,
        attempts=3,
    )

    rendered = json.dumps(record)
    for secret in ("abc", "hf_xxxxx", "alice", "/private"):
        assert secret not in rendered
    assert record["nested"]["count"] == 7
    assert record["values"][1] == ["<path>", True, 2.5]
    assert record["enabled"] is True
    assert record["attempts"] == 3


def test_diagnostics_never_emits_plain_runtime_key(monkeypatch):
    record = _record(monkeypatch, metadata={"ok": True})

    assert record["runtime_key"] != "raw-runtime-key"
    assert "raw-runtime-key" not in json.dumps(record)


def test_sanitize_data_redacts_secret_values_from_original_field_names():
    secret_fields = (
        "token",
        "hf_token",
        "hf-token",
        "huggingface_token",
        "huggingface-token",
        "access_token",
        "refresh_token",
        "auth_token",
        "id_token",
        "oauth_token",
        "confirmation_token",
        "confirmationToken",
        "password",
        "passwd",
        "secret",
        "client_secret",
        "api_key",
        "api-key",
        "authorization",
    )
    payload = {
        "nested": [
            {name: f"plain-value-{index}" for index, name in enumerate(secret_fields)},
            {"token_count": 17, "tokenizer": "synthetic", "enabled": True},
        ]
    }

    sanitized = diagnostics.sanitize_data(payload)
    secret_values = sanitized["nested"][0]
    assert all(secret_values[name] == "<redacted>" for name in secret_fields)
    assert sanitized["nested"][1] == {
        "token_count": 17,
        "tokenizer": "synthetic",
        "enabled": True,
    }


def test_named_diagnostic_fields_use_key_based_secret_redaction(monkeypatch):
    record = _record(
        monkeypatch,
        hf_token="plain-value",
        client_secret="another-plain-value",
        token_count=9,
    )

    assert record["hf_token"] == "<redacted>"
    assert record["client_secret"] == "<redacted>"
    assert record["token_count"] == 9
