"""Paridade Postgres × Snowflake: chama cada endpoint nos dois engines (TestClient) e compara as respostas.

Comparação estrita por padrão: listas em ordem, chaves como vieram, strings sem conversão; só números
(int/float) viram float arredondado a 6 casas. Um caso pode ser `unordered: true` (a query não tem ORDER BY)
e `allow_empty: true` (resposta vazia legítima). Resposta vazia sem `allow_empty` falha: comparar dois vazios
não prova nada.
"""
from __future__ import annotations

import functools
import json
import math
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import pytest
import yaml
from fastapi.testclient import TestClient

HERE = Path(__file__).parent
CFG = yaml.safe_load((HERE / "cases.yaml").read_text())
PARAMS = {**{k: v for k, v in CFG.items() if k not in ("cases", "periodo")}, **CFG["periodo"]}


def _case(raw) -> dict:
    c = {"path": raw} if isinstance(raw, str) else dict(raw)
    c.setdefault("unordered", False)
    c.setdefault("allow_empty", False)
    c["path"] = c["path"].format(**PARAMS)
    return c


CASES = [_case(c) for c in CFG["cases"]]
REPORT = HERE / "report.md"
RESULTS: dict = {}


def norm(v):
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    if isinstance(v, list):
        return [norm(x) for x in v]
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
        return round(float(v), 6)
    return v


def sort_deep(v):
    if isinstance(v, dict):
        return {k: sort_deep(x) for k, x in v.items()}
    if isinstance(v, list):
        return sorted((sort_deep(x) for x in v), key=lambda x: json.dumps(x, sort_keys=True, default=str))
    return v


def same(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, abs_tol=1e-6, rel_tol=1e-9)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def size(v):
    """Tamanho no nível de cima: comprimento da lista ou nº de chaves (com o tamanho das listas internas)."""
    if isinstance(v, list):
        return str(len(v))
    if isinstance(v, dict):
        inner = ", ".join(f"{k}={len(x)}" for k, x in v.items() if isinstance(x, list))
        return f"{len(v)} chaves" + (f" ({inner})" if inner else "")
    return None if v is None else "1"


def is_empty(v, echo=None) -> bool:
    """Vazio: None, "", 0, [] ou dict cujos valores são todos vazios (ex.: KPIs zerados).

    `echo` são os parâmetros da query string: chaves do dict que só repetem um parâmetro (limite, offset)
    não contam como conteúdo.
    """
    echo = echo or {}
    if v is None or v == "" or v == []:
        return True
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return v == 0
    if isinstance(v, dict):
        return all(is_empty(x) for k, x in v.items() if not (k in echo and str(x) == echo[k]))
    return False


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


def compare(pg, sf, unordered: bool):
    """Devolve (ok, motivo)."""
    a, b = norm(pg), norm(sf)
    if unordered:
        return (True, "") if same(sort_deep(a), sort_deep(b)) else (False, "diverge (sem ordem)")
    if same(a, b):
        return True, ""
    if same(sort_deep(a), sort_deep(b)):
        return False, "differs only in order"
    return False, "diverge"


@pytest.mark.parametrize("case", CASES, ids=[f"{c['path'].split('/')[2]}-{i}" for i, c in enumerate(CASES)])
def test_paridade(monkeypatch, case):
    path = case["path"]
    s_pg, pg = call(monkeypatch, "postgres", path)
    s_sf, sf = call(monkeypatch, "snowflake", path)
    echo = dict(parse_qsl(urlsplit(path).query))
    empty_pg = s_pg == 200 and is_empty(pg, echo)
    empty_sf = s_sf == 200 and is_empty(sf, echo)
    if s_pg != 200:
        ok, why = False, f"postgres {s_pg}"
    elif empty_pg and not case["allow_empty"]:
        ok, why = False, "postgres vazio sem allow_empty"
    elif s_sf != 200:
        ok, why = False, f"snowflake {s_sf}"
    elif empty_pg and empty_sf and not case["allow_empty"]:
        ok, why = False, "os dois lados vazios sem allow_empty"
    else:
        ok, why = compare(pg, sf, case["unordered"])
    RESULTS[path] = {"ok": ok, "why": why, "pg": s_pg, "sf": s_sf,
                     "size_pg": size(pg) if s_pg == 200 else None, "size_sf": size(sf) if s_sf == 200 else None,
                     "empty_pg": empty_pg, "flags": ",".join(k for k in ("unordered", "allow_empty") if case[k])}
    assert s_pg == 200, f"postgres {s_pg}: {pg}"
    assert not (empty_pg and not case["allow_empty"]), f"postgres devolveu vazio em {path}; use allow_empty"
    assert s_sf == 200, f"snowflake {s_sf}: {sf}"
    assert ok, f"{why} em {path}"


def teardown_module(module):
    linhas = ["# Paridade Postgres × Snowflake", "",
              "| Endpoint | flags | PG | SF | tam PG | tam SF | PG vazio | OK |", "|---|---|---|---|---|---|---|---|"]
    for p, r in RESULTS.items():
        linhas.append(f"| `{p}` | {r['flags']} | {r['pg']} | {r['sf']} | {r['size_pg']} | {r['size_sf']} | "
                      f"{'sim' if r['empty_pg'] else ''} | {'✅' if r['ok'] else '❌ ' + r['why']} |")
    total = sum(1 for r in RESULTS.values() if r["ok"])
    pg200 = sum(1 for r in RESULTS.values() if r["pg"] == 200)
    linhas += ["", f"**{total}/{len(RESULTS)} iguais** · Postgres 200: {pg200}/{len(RESULTS)}"]
    REPORT.write_text("\n".join(linhas) + "\n")
