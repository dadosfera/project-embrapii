import pytest

from backend.cache import query_cache


@pytest.fixture(autouse=True)
def _reset_query_cache():
    """Isola os testes do cache global: TTL=0 e sem entradas residuais entre testes."""
    original_ttl = query_cache.ttl
    query_cache.ttl = 0
    query_cache._data.clear()
    yield
    query_cache._data.clear()
    query_cache.ttl = original_ttl


@pytest.fixture(autouse=True)
def _reset_snowflake_secret():
    """O secret do Snowflake fica em memória no processo; cada teste começa sem ele."""
    from backend import snowflake_conn

    snowflake_conn._secret_cache = None
    yield
    snowflake_conn._secret_cache = None
