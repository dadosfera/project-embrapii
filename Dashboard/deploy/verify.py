#!/usr/bin/env python3
"""Verifica o data app publicado: health, engine e um GET com dado por router."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dadosfera_client import Dadosfera  # noqa: E402

M = json.loads((Path(__file__).parent / "manifest.json").read_text())
URL = M["dataapp_url"].rstrip("/")
CHECKS = [
    ("/health", lambda j: j.get("status") == "ok"),
    ("/health/database", lambda j: j.get("engine") == "snowflake" and j.get("status") == "ok"),
    ("/api/leitos/opcoes", lambda j: bool(j)),
    ("/api/medicamentos/busca?q=dipirona&limite=5", lambda j: len(j) > 0),
    ("/api/compras/kpis?data_inicio=2024-01-01&data_fim=2024-12-31", lambda j: bool(j)),
    ("/api/fornecedores/mapa-por-uf?data_inicio=2024-01-01&data_fim=2024-12-31", lambda j: len(j) > 0),
]


def _json(r):
    try:
        return r.json()
    except ValueError:
        return None


def main() -> None:
    d = Dadosfera(); d.login()
    ok = True
    for path, check in CHECKS:
        r = d.raw("GET", URL + path, timeout=120)
        j = _json(r)
        good = r.status_code == 200 and j is not None and bool(check(j))
        ok &= good
        print(("OK  " if good else "FAIL"), r.status_code, path, "" if good else r.text[:200])
    r = d.raw("GET", URL + "/", timeout=60)
    good = r.status_code == 200 and "window.__APP_BASE__" in r.text
    ok &= good
    print(("OK  " if good else "FAIL"), r.status_code, "/ (index com prefixo)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
