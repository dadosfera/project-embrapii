from __future__ import annotations

import functools
import json
import math
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

HERE = Path(__file__).parent
CFG = yaml.safe_load((HERE / "cases.yaml").read_text())
CASES = [c.format(catmat=CFG["catmat"], **CFG["periodo"]) for c in CFG["cases"]]
REPORT = HERE / "report.md"
RESULTS: dict = {}


def norm(v):
    if isinstance(v, dict):
        return {k.lower(): norm(x) for k, x in sorted(v.items())}
    if isinstance(v, list):
        return sorted((norm(x) for x in v), key=lambda x: json.dumps(x, sort_keys=True, default=str))
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
        return round(float(v), 6)
    if isinstance(v, str):
        try:
            return round(float(v), 6)
        except ValueError:
            return v.replace("T00:00:00", "").replace("+00:00", "")
    return v


def clear_router_caches() -> None:
    """Os routers têm lru_cache próprios (ex.: leitos /opcoes e /painel) cuja chave não inclui o engine.

    Sem limpar, a chamada Snowflake devolveria o resultado em cache da chamada Postgres.
    """
    from backend.api import compras, fornecedores, leitos, medicamentos

    for mod in (compras, fornecedores, leitos, medicamentos):
        for obj in vars(mod).values():
            if isinstance(obj, functools._lru_cache_wrapper):
                obj.cache_clear()


def call(monkeypatch, engine: str, path: str):
    monkeypatch.setenv("DB_ENGINE", engine)
    from backend.main import app

    clear_router_caches()
    r = TestClient(app, raise_server_exceptions=False).get(path)
    return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text)


def same(a, b) -> bool:
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, abs_tol=1e-6, rel_tol=1e-9)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


@pytest.mark.parametrize("path", CASES, ids=[f"{c.split('/')[2]}-{i}" for i, c in enumerate(CASES)])
def test_paridade(monkeypatch, path):
    s_pg, pg = call(monkeypatch, "postgres", path)
    s_sf, sf = call(monkeypatch, "snowflake", path)
    ok = s_pg == s_sf == 200 and same(norm(pg), norm(sf))
    RESULTS[path] = (ok, s_pg, s_sf)
    assert s_pg == 200, f"postgres {s_pg}: {pg}"
    assert s_sf == 200, f"snowflake {s_sf}: {sf}"
    assert ok, f"divergência em {path}"


def teardown_module(module):
    linhas = ["# Paridade Postgres × Snowflake", "", "| Endpoint | PG | SF | OK |", "|---|---|---|---|"]
    for p, (ok, a, b) in RESULTS.items():
        linhas.append(f"| `{p}` | {a} | {b} | {'✅' if ok else '❌'} |")
    total = sum(1 for ok, *_ in RESULTS.values() if ok)
    linhas += ["", f"**{total}/{len(RESULTS)} iguais**"]
    REPORT.write_text("\n".join(linhas) + "\n")
