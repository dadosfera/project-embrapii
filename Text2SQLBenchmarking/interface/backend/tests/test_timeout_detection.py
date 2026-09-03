import pytest

from interface.backend.domain.artifacts import (
    is_historical_timeout,
    normalize_timeout_message,
)


@pytest.mark.parametrize(
    "message",
    [
        "Erro: A query excedeu o tempo limite de 30 segundos.",
        "Erro: A query excedeu o tempo limite de 30.5 segundos.",
        "  ERRO:   A QUERY excedeu\n o tempo limite de 30 segundos.  ",
        "Ｅｒｒｏ： Ａ ｑｕｅｒｙ ｅｘｃｅｄｅｕ ｏ ｔｅｍｐｏ ｌｉｍｉｔｅ ｄｅ ３０．５ ｓｅｇｕｎｄｏｓ．",
    ],
)
def test_recognizes_normalized_historical_timeout(message):
    assert is_historical_timeout(message)


@pytest.mark.parametrize(
    "message",
    [
        "timeout",
        "tempo limite",
        "statement timeout",
        "Erro: A query excedeu o tempo limite de 30 segundos. detalhe",
        "prefixo Erro: A query excedeu o tempo limite de 30 segundos.",
        "Erro: A query excedeu o tempo limite de 30,5 segundos.",
        "Erro: A query excedeu o tempo limite de trinta segundos.",
        None,
    ],
)
def test_rejects_partial_or_unconfirmed_messages(message):
    assert not is_historical_timeout(message)


def test_rejects_unicode_digits_not_normalized_to_ascii():
    assert not is_historical_timeout(
        "Erro: A query excedeu o tempo limite de ٣٠ segundos."
    )


def test_normalization_is_explicit_and_deterministic():
    assert normalize_timeout_message("  ERRO:\nA   QUERY  ") == "erro: a query"
