from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from types import SimpleNamespace
from unittest.mock import Mock
import sys
from uuid import UUID

import pytest

from interface.backend.adapters.postgres_chat import PostgreSqlChatExecutor
from interface.backend.chat.query import ChatServiceError
from interface.backend.domain.capabilities import ConfigurationSelection


def _run(monkeypatch, rows=(), *, execute_error=None, fetch_error=None, rollback_error=None, close_error=None):
    cursor=Mock(); cursor.description=[("x",)]; cursor.fetchmany.side_effect=fetch_error or (lambda n: list(rows)); cursor.execute.side_effect=execute_error
    connection=Mock(); connection.cursor.return_value=cursor; connection.rollback.side_effect=rollback_error; connection.close.side_effect=close_error
    monkeypatch.setitem(sys.modules,"psycopg2",SimpleNamespace(connect=Mock(return_value=connection)))
    import src.utilitis
    monkeypatch.setattr(src.utilitis,"get_db_config",lambda _: ({"user":"u","password":"p","host":"h","port":"1","db_name":"d"},None))
    executor=PostgreSqlChatExecutor(timeout_ms=123); config=ConfigurationSelection("sih_database","raw_model","m","default")
    return executor,config,cursor,connection

@pytest.mark.parametrize("count,expected",[(0,(0,0,False)),(200,(200,200,False)),(201,(201,200,True))])
def test_postgres_executor_limits_and_session(monkeypatch,count,expected):
    executor,config,cursor,connection=_run(monkeypatch,[(i,) for i in range(count)])
    result=executor.execute(config,"SELECT approved")
    assert (result.row_count,result.displayed_row_count,result.truncated)==expected
    connection.set_session.assert_called_once_with(readonly=True,autocommit=False)
    assert cursor.execute.call_args_list[0].args[0]=="SET LOCAL statement_timeout = %s"
    assert cursor.execute.call_args_list[1].args[0]=="SELECT approved"; cursor.fetchmany.assert_called_once_with(201); cursor.close.assert_called_once(); connection.close.assert_called_once()

def test_postgres_executor_closes_on_execute_fetch_rollback_and_close_failures(monkeypatch):
    for kwargs in ({"execute_error":RuntimeError()},{"fetch_error":RuntimeError()},{"rollback_error":RuntimeError()},{"close_error":RuntimeError()}):
        executor,config,cursor,connection=_run(monkeypatch,**kwargs)
        if "rollback_error" in kwargs or "close_error" in kwargs: assert executor.execute(config,"SELECT 1").row_count==0
        else:
            with pytest.raises(ChatServiceError): executor.execute(config,"SELECT 1")
        cursor.close.assert_called_once(); connection.close.assert_called_once()


def test_postgres_executor_serializes_public_values_without_leaking_objects(monkeypatch):
    class Marker(Enum):
        VALUE = "enum-value"

    values = (
        Decimal("12.50"),
        datetime(2026, 8, 10, 12, 30, tzinfo=timezone.utc),
        UUID("12345678-1234-5678-1234-567812345678"),
        b"synthetic-binary",
        Marker.VALUE,
        object(),
    )
    executor, config, _, _ = _run(monkeypatch, [values])

    result = executor.execute(config, "SELECT approved")

    assert result.displayed_rows == ((
        "12.50",
        "2026-08-10T12:30:00+00:00",
        "12345678-1234-5678-1234-567812345678",
        "[binary data]",
        "enum-value",
        "[unsupported value]",
    ),)
