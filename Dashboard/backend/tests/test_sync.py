import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def referenced_relations():
    text = "\n".join(p.read_text() for p in (ROOT / "backend" / "api").glob("*.py"))
    sql_refs = set(re.findall(r"(?i)\b(?:from|join)\s+([a-z_][a-z0-9_]*)\s", text))
    ctes = set(re.findall(r"(?i)\b([a-z_][a-z0-9_]*)\s+as\s+(?:materialized\s+)?\(", text))
    py_imports = {"backend", "datetime", "fastapi", "functools", "time", "typing", "exc", "lateral"}
    return {r.lower() for r in sql_refs} - {c.lower() for c in ctes} - py_imports


def test_tables_txt_cobre_routers():
    tables = set((ROOT / "scripts" / "tables.txt").read_text().split())
    faltando = referenced_relations() - tables
    assert not faltando, f"routers citam relações fora de scripts/tables.txt: {sorted(faltando)}"
