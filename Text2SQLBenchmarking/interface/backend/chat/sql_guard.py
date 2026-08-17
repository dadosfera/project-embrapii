"""Conservative structural PostgreSQL read-only policy."""
from __future__ import annotations

import re
import sqlglot
from sqlglot import exp


class UnsafeSqlError(ValueError):
    """Public callers deliberately receive no parser detail."""


_WRITE_NODES = tuple(getattr(exp, name) for name in ("Insert", "Update", "Delete", "Merge", "Create", "Alter", "Drop", "Command", "Grant", "Revoke") if hasattr(exp, name))
_EXACT_FUNCTIONS = frozenset({"nextval", "setval", "set_config", "pg_sleep", "pg_sleep_for", "pg_sleep_until", "pg_notify", "notify", "pg_cancel_backend", "pg_terminate_backend", "pg_reload_conf", "pg_rotate_logfile", "pg_switch_wal", "pg_create_restore_point", "pg_promote", "pg_backup_start", "pg_backup_stop", "pg_start_backup", "pg_stop_backup", "pg_create_physical_replication_slot", "pg_create_logical_replication_slot", "pg_drop_replication_slot", "pg_replication_slot_advance", "pg_logical_emit_message", "pg_replication_origin_advance", "dblink", "dblink_exec", "dblink_send_query", "dblink_connect", "dblink_connect_u", "pg_read_file", "pg_read_binary_file", "pg_ls_dir", "pg_stat_file", "lo_creat", "lo_create", "lo_import", "lo_export", "lo_unlink"})
_PREFIXES = ("pg_advisory_", "pg_try_advisory_", "dblink_", "pg_read_", "pg_write_", "pg_file_", "pg_ls_", "lo_")


def _function_name(node: exp.Func) -> str:
    raw = getattr(node, "name", "") or node.sql_name()
    return raw.lower().split(".")[-1]


def approve_read_only(sql: str) -> str:
    text = sql.strip()
    if not text:
        raise UnsafeSqlError()
    try:
        statements = sqlglot.parse(text, read="postgres")
    except Exception as exc:
        raise UnsafeSqlError() from exc
    if len(statements) != 1 or statements[0] is None:
        raise UnsafeSqlError()
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.Subquery)) or any(isinstance(node, _WRITE_NODES) for node in tree.walk()):
        raise UnsafeSqlError()
    for select in tree.find_all(exp.Select):
        if select.args.get("into") is not None or select.args.get("locks"):
            raise UnsafeSqlError()
    for function in tree.find_all(exp.Func):
        name = _function_name(function)
        if name == "lowrite" or name in _EXACT_FUNCTIONS or name.startswith(_PREFIXES) or name.startswith("pg_stat_reset"):
            raise UnsafeSqlError()
    return text[:-1].rstrip() if text.endswith(";") else text
