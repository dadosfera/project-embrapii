#!/usr/bin/env python3
"""Escreve a camada editorial (nome, descrição, tags, docs, certificação) dos 17 ativos do schema EMBRAPII_DATASUS no Catálogo da Dadosfera.

Só EDITA os ativos catalogados automaticamente; nunca cria dataset (POST /catalog) e nunca envia location/embed/data_asset_type.
Idempotente: compara com o estado atual e só escreve o que mudou. Dry-run por padrão.

Uso:
  DADOSFERA_ENV_FILE=/caminho/.env python3 catalog/document_assets.py            # dry-run (mostra o diff)
  DADOSFERA_ENV_FILE=/caminho/.env python3 catalog/document_assets.py --apply    # grava
Credenciais: DADOSFERADEMO_USER / DADOSFERADEMO_PASSWORD (ou DADOSFERA_USERNAME / DADOSFERA_PASSWORD) no ambiente ou no env file.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quill_html import md_to_quill_html  # noqa: E402

HERE = Path(__file__).resolve().parent
CONTENT = HERE / "content"
MANIFEST = HERE / "catalog_manifest.json"
MAESTRO = os.getenv("MAESTRO_BASE_URL", "https://maestro.dadosfera.ai")
SCHEMA = "EMBRAPII_DATASUS"
EDITORIAL = ("display_name", "description", "tags", "comment", "certification_status")


def load_env(path: str | None) -> dict[str, str]:
    env: dict[str, str] = {}
    for p in [path, ".env"]:
        if p and Path(p).exists():
            for line in open(p):
                m = re.match(r'^\s*([A-Za-z_]\w*)=(.*)$', line.rstrip("\n"))
                if m:
                    env.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
    return env


class Maestro:
    def __init__(self) -> None:
        env = load_env(os.getenv("DADOSFERA_ENV_FILE"))
        pick = lambda *k: next((os.getenv(x) or env.get(x) for x in k if os.getenv(x) or env.get(x)), None)  # noqa: E731
        self.user = pick("DADOSFERA_USERNAME", "DADOSFERADEMO_USER")
        self.pwd = pick("DADOSFERA_PASSWORD", "DADOSFERADEMO_PASSWORD")
        if not self.user or not self.pwd:
            raise SystemExit("credenciais ausentes (DADOSFERADEMO_USER/PASSWORD no ambiente ou em DADOSFERA_ENV_FILE)")
        self.s = requests.Session()
        self.s.headers["Accept"] = "application/json"
        self.exp = 0.0

    def login(self) -> None:
        r = self.s.post(f"{MAESTRO}/auth/sign-in", json={"username": self.user, "password": self.pwd}, timeout=30)
        r.raise_for_status()
        self.s.headers["Authorization"] = r.json()["tokens"]["accessToken"]
        self.exp = time.time() + 25 * 60

    def _send(self, method: str, path: str, **kw: Any) -> requests.Response:
        for attempt in range(4):  # o Maestro derruba conexões esporadicamente
            try:
                return self.s.request(method, f"{MAESTRO}{path}", timeout=120, **kw)
            except requests.ConnectionError:
                if attempt == 3:
                    raise
                time.sleep(2 * (attempt + 1))
        raise RuntimeError("unreachable")

    def req(self, method: str, path: str, **kw: Any) -> Any:
        if time.time() > self.exp:
            self.login()
        r = self._send(method, path, **kw)
        if r.status_code == 401:
            self.login()
            r = self._send(method, path, **kw)
        if not r.ok:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
        return r.json() if r.content and "json" in r.headers.get("content-type", "") else {}

    def search(self, term: str) -> list[dict]:
        """Busca paginada por `page`. NUNCA passar `limit` ao endpoint: devolve vazio."""
        out, page = [], 1
        while True:
            j = self.req("GET", "/catalog", params={"search": term, "page": page})
            batch = j.get("data_assets", [])
            out += batch
            if not batch or len(out) >= j.get("total", 0):
                return out
            page += 1

    def asset(self, aid: str) -> dict:
        a = self.req("GET", f"/catalog/data-asset/{aid}")
        return a.get("data_asset", a)

    def docs(self, aid: str) -> str:
        try:
            return (self.req("GET", f"/catalog/data-asset/{aid}/docs") or {}).get("docs") or ""
        except RuntimeError:
            return ""


def parse_content(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise SystemExit(f"{path.name}: front-matter ausente")
    fm = dict(re.match(r"^(\w+):\s*(.*)$", ln).groups() for ln in m.group(1).splitlines() if ln.strip())
    return {
        "table": fm["table"],
        "display_name": fm["display_name"],
        "description": fm["description"],
        "tags": [t.strip() for t in fm["tags"].split(",") if t.strip()],
        "docs": md_to_quill_html(m.group(2)),
    }


def resolve_ids(api: Maestro, wanted: list[str]) -> dict[str, str]:
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"schema": SCHEMA, "assets": {}}
    ids = manifest["assets"]
    if all(t in ids for t in wanted):
        return ids
    for x in api.search("EMBRAPII"):
        if x.get("table_schema") == SCHEMA and x.get("table_name") in wanted and x["id"] not in ids.values():
            ids[x["table_name"]] = x["id"]
    missing = [t for t in wanted if t not in ids]
    if missing:
        print(f"ATENCAO: ativos não encontrados no catálogo: {missing}")
    MANIFEST.write_text(json.dumps({"schema": SCHEMA, "assets": dict(sorted(ids.items()))}, indent=2, ensure_ascii=False) + "\n")
    return ids


CATALOG_URL = "https://app.dadosfera.ai/en-US/catalog/data-assets/{}"  # rota do front (a mesma gravada pela demo Porto no Storage Explorer)
DEPLOY_MANIFEST = HERE.parent / "deploy" / "manifest.json"  # somente leitura


def sync_dataapp(api: Maestro, ids: dict[str, str], apply: bool, failures: list[str]) -> None:
    """Ativo MANUAL do data app (não existe ativo automático para data app). Cria só se o manifesto não tiver o id."""
    src = parse_dataapp()
    url = json.loads(DEPLOY_MANIFEST.read_text())["dataapp_url"]
    md = src["md"].replace("{{url}}", url)
    md = re.sub(r"\{\{asset:(\w+)\}\}", lambda m: CATALOG_URL.format(ids[m.group(1)]), md)
    docs = md_to_quill_html(md)
    manifest = json.loads(MANIFEST.read_text())
    aid = manifest.get("dataapp")
    if not aid:
        dup = [x for x in api.search("Dashboard EMBRAPII") if x.get("data_asset_type") == "dataapp" and x.get("display_name") == src["display_name"]]
        aid = dup[0]["id"] if dup else None
    meta = {"display_name": src["display_name"], "description": src["description"], "tags": src["tags"], "location": src["location"],
            "external_url": url, "embed": {"url": url}, "data_asset_type": "dataapp"}
    if not aid:
        print(f"{'CREATE' if apply else 'DIFF '} dataapp  (novo ativo manual)")
        if not apply:
            return
        try:
            aid = api.req("POST", "/catalog", json={**meta, "name": src["display_name"]}).get("data_asset", {})["id"]
        except RuntimeError as e:
            failures.append(f"dataapp: {e}")
            return
        manifest["dataapp"] = aid
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        cur: dict = {}
    else:
        cur = api.asset(aid)
    changes = [k for k in ("display_name", "description", "location", "external_url") if cur.get(k) != meta[k]]
    if sorted(cur.get("tags") or []) != sorted(meta["tags"]):
        changes.append("tags")
    if (cur.get("embed") or {}).get("url") != url:
        changes.append("embed")
    if api.docs(aid).strip() != docs.strip():
        changes.append("docs")
    if cur.get("certification_status") != "approved":
        changes.append("certification")
    print(f"{'APPLY' if apply else 'DIFF '} dataapp {aid}  mudanças: {', '.join(changes) or 'nenhuma'}")
    if not apply or not changes:
        return
    try:
        api.req("PUT", f"/catalog/data-asset/{aid}", json=meta)
        api.req("POST", f"/catalog/data-asset/{aid}/docs", params={"asset_type": "dataapp"}, json={"docs": docs})
        api.req("PUT", f"/catalog/data-asset/{aid}/certification-status", json={"certification_status": "approved"})
    except RuntimeError as e:
        failures.append(f"dataapp: {e}")


def parse_dataapp() -> dict:
    text = (CONTENT / "dataapp" / "dashboard-embrapii.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    fm = dict(re.match(r"^(\w+):\s*(.*)$", ln).groups() for ln in m.group(1).splitlines() if ln.strip())
    fm["tags"] = [t.strip() for t in fm["tags"].split(",")]
    fm["md"] = m.group(2)
    return fm


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="grava no catálogo (padrão: dry-run)")
    ap.add_argument("--only", help="tabelas separadas por vírgula (ex.: CATMAT,PRODUTO)")
    ap.add_argument("--no-certify", action="store_true")
    args = ap.parse_args()

    items = {c["table"]: c for c in map(parse_content, sorted(CONTENT.glob("*.md")))}
    only = {t.strip().upper() for t in args.only.split(",")} if args.only else None
    wanted = [t for t in items if not only or t in only]  # --only DATAAPP seleciona só o ativo do data app
    api = Maestro()
    api.login()
    ids = resolve_ids(api, list(items))

    bk = HERE / f"backup_{dt.date.today():%Y%m%d}.json"
    write_bk = args.apply and not bk.exists()  # o backup do dia guarda o estado ANTERIOR; reexecuções não o sobrescrevem
    backup: dict[str, Any] = {}
    failures: list[str] = []
    for t in wanted:
        aid = ids.get(t)
        if not aid:
            failures.append(f"{t}: sem id")
            continue
        cur = api.asset(aid)
        if cur.get("table_schema") != SCHEMA or cur.get("table_name") != t:
            failures.append(f"{t}: id {aid} não confere com o schema/tabela")
            continue
        cur_docs = api.docs(aid)
        backup[t] = {"id": aid, **{k: cur.get(k) for k in EDITORIAL}, "docs": cur_docs}
        if write_bk:
            bk.write_text(json.dumps(backup, indent=2, ensure_ascii=False))
        new = items[t]
        changes = [k for k in ("display_name", "description") if cur.get(k) != new[k]]
        if sorted(cur.get("tags") or []) != sorted(new["tags"]):
            changes.append("tags")
        if cur_docs.strip() != new["docs"].strip():
            changes.append("docs")
        if not args.no_certify and cur.get("certification_status") != "approved":
            changes.append("certification")
        print(f"{'APPLY' if args.apply else 'DIFF '} {t:30s} {aid}  mudanças: {', '.join(changes) or 'nenhuma'}")
        if not args.apply or not changes:
            continue
        try:
            meta = {k: new[k] for k in ("display_name", "description", "tags") if k in changes}
            if meta:
                api.req("PUT", f"/catalog/data-asset/{aid}", json=meta)
            if "docs" in changes:
                api.req("POST", f"/catalog/data-asset/{aid}/docs", params={"asset_type": "dataset"}, json={"docs": new["docs"]})
            if "certification" in changes:
                try:
                    api.req("PUT", f"/catalog/data-asset/{aid}/certification-status", json={"certification_status": "approved"})
                except RuntimeError as e:
                    print(f"  [aviso] certificação rejeitada para {t}: {e}")
        except RuntimeError as e:
            failures.append(f"{t}: {e}")
            print(f"  [falhou] {t}: {e}")

    if not only or "DATAAPP" in only:
        sync_dataapp(api, ids, args.apply, failures)

    if write_bk:
        print(f"backup: {bk}")
    if not args.apply:
        print("\n(dry-run) use --apply para gravar")
    if failures:
        print("\nFALHAS:\n  " + "\n  ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
