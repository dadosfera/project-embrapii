#!/usr/bin/env python3
"""Deploy do Dashboard DATASUS como standalone service no Módulo de Inteligência (Orchest v2026.08+), tenant dadosferademo (demo2).
Passos: projeto → upload backend/ + frontend/dist/ → ambiente (build aguardado) → pipeline com o serviço `dataapp` → standalone service.
O upload vem antes do ambiente porque o environment_setup.sh instala /project-dir/backend/requirements.txt.
Adaptado de kine-gest-ddf-oic/apps/oic-visitors/deploy/deploy_service.py.
Uso: DADOSFERA_ENV_FILE=/caminho/.env python3 deploy/deploy_service.py --start [--skip-upload] [--dry-run]
Pré-requisito: frontend/dist buildado (`cd frontend && npm run build`; o prefixo do Orchest chega em runtime).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dadosfera_client import Dadosfera  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]  # Dashboard/
MANIFEST = ROOT / "deploy" / "manifest.json"
PROJECT = os.getenv("EMBRAPII_PROJECT_NAME", "embrapii-dashboard-datasus")
PROJECT_DESCRIPTION = ("Dashboard Dados em Saúde (projeto EMBRAPII DCC/UFMG): medicamentos, compras, leitos e "
                       "fornecedores do DATASUS. Lê o Snowflake EMBRAPII_DATASUS.")
ENV_NAME = "embrapii-dashboard"
BASE_IMAGE = os.getenv("ORCHEST_BASE_IMAGE", "dadosfera/base-kernel-py")
SECRET_ID = os.getenv("SNOWFLAKE_SECRET_ID", "prd/root/snowflake_credentials/dadosferademo")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "DADOSFERA_PRD_DADOSFERADEMO")
SERVICE = "dataapp"; PORT = 8000; PIPELINE = "embrapii_dataapp"
PIPELINE_TITLE = "Data App · Dashboard DATASUS (EMBRAPII)"
OUT = ROOT / "frontend" / "dist"
UPLOAD_ROOTS = [ROOT / "backend"]  # sobe backend/ inteiro (lição Porto: arquivo faltando = CrashLoopBackOff)
EXCLUDE = ("__pycache__", "tests", ".pytest_cache", ".ruff_cache")
ENV_BUILD_TIMEOUT = 20 * 60; ENV_BUILD_POLL = 20; ENV_BUILD_BLIND_WAIT = 5 * 60
UPLOAD_ATTEMPTS = 2


def upload_files() -> List[Path]:
    """backend/** (menos EXCLUDE, .env e dotfiles) + frontend/dist/**, como caminhos absolutos locais."""
    files: List[Path] = []
    for root in UPLOAD_ROOTS:
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            parts = p.relative_to(root).parts
            if any(part.startswith(".") or part in EXCLUDE for part in parts) or p.name == ".env":
                continue
            files.append(p)
    files += sorted(p for p in OUT.rglob("*") if p.is_file())
    return files


def service_doc(pl_uuid: str, env_uuid: str) -> dict:
    return {"name": PIPELINE_TITLE, "uuid": pl_uuid, "version": "1.2.3", "parameters": {},
            "settings": {"auto_eviction": True, "data_passing_memory_size": "1GB", "max_steps_parallelism": 1}, "steps": {},
            "services": {SERVICE: {
                "name": SERVICE, "image": f"environment@{env_uuid}", "command": "bash",
                "args": f"-c 'umask 002 && cd /project-dir && uvicorn backend.main:app --host 0.0.0.0 --port {PORT}'",
                "binds": {"/project-dir": "/project-dir", "/data": "/data"}, "ports": [PORT], "exposed": True,
                "preserve_base_path": True, "requires_authentication": False, "scope": ["interactive", "noninteractive"], "order": 1,
                "env_variables": {
                    "DB_ENGINE": "snowflake",
                    "SNOWFLAKE_SECRET_ID": SECRET_ID,
                    "SNOWFLAKE_DATABASE": SNOWFLAKE_DATABASE,
                    "SNOWFLAKE_SCHEMA": "EMBRAPII_DATASUS",
                    "FRONTEND_DIST": "/project-dir/frontend/dist",
                    "APP_BASE_PATH": f"/$BASE_PATH_PREFIX_{PORT}",
                    "QUERY_CACHE_TTL_SECONDS": "3600",
                }}}}


def _find_build(payload, env_uuid: str) -> Optional[dict]:
    """Defensivo: os builds podem vir como lista no topo ou em `environment_image_builds`."""
    builds = payload.get("environment_image_builds") if isinstance(payload, dict) else payload
    if not isinstance(builds, list): return None
    mine = [b for b in builds if isinstance(b, dict) and b.get("environment_uuid") == env_uuid]
    if not mine: return None
    return sorted(mine, key=lambda b: str(b.get("requested_time") or b.get("started_time") or ""))[-1]


class Deployer:
    def __init__(self) -> None:
        self.d = Dadosfera(); self.d.login()
        self.m = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}

    def save(self) -> None: MANIFEST.write_text(json.dumps(self.m, indent=2, ensure_ascii=False) + "\n")

    def project(self) -> str:
        projs = self.d.orchest_get("/async/projects", timeout=120)
        p = next((p for p in projs if p.get("path") == PROJECT), None)
        if not p:
            self.d.orchest_post("/async/projects", json={"name": PROJECT, "description": PROJECT_DESCRIPTION}); time.sleep(3)  # v2026.08.26+ exige description
            projs = self.d.orchest_get("/async/projects", timeout=120); p = next(p for p in projs if p.get("path") == PROJECT)
        self.m["project_uuid"] = p["uuid"]; print("project =", p["uuid"]); return p["uuid"]

    def environment(self, pu: str) -> Tuple[str, bool]:
        """Devolve (environment_uuid, rebuild). Ambiente novo ou com setup_script alterado sai com o build disparado."""
        envs = self.d.orchest_get(f"/store/environments/{pu}")
        e = next((e for e in envs if e.get("name") == ENV_NAME), None); created = False
        setup = (ROOT / "deploy" / "environment_setup.sh").read_text()
        spec = {"base_image": BASE_IMAGE, "gpu_support": "false", "language": "python", "name": ENV_NAME, "setup_script": setup}
        if not e:
            e = self.d.orchest_post(f"/store/environments/{pu}/new", json={"environment": {**spec, "uuid": "new"}}); created = True
        elif e.get("setup_script") != setup:  # setup mudou: atualiza e rebuilda
            self.d.req("PUT", f"{self.d.orchest}/store/environments/{pu}/{e['uuid']}", json={"environment": {**spec, "uuid": e["uuid"]}}); created = True
            print("environment setup_script updated")
        if created:
            self.d.orchest_post("/catch/api-proxy/api/environment-builds", json={"environment_image_build_requests": [{"project_uuid": pu, "environment_uuid": e["uuid"]}]})
            print("environment build started")
        self.m["environment_uuid"] = e["uuid"]; print("environment =", e["uuid"]); return e["uuid"], created

    def wait_environment_build(self, pu: str, env_uuid: str) -> None:
        """Poll até SUCCESS (ou falha explícita). Formato de resposta desconhecido → espera cega."""
        t0 = time.time(); shape_known = False
        while time.time() - t0 < ENV_BUILD_TIMEOUT:
            try:
                # v2026.08: só a rota most-recent responde JSON; a coleção pura devolve o HTML da SPA.
                payload = self.d.orchest_get(f"/catch/api-proxy/api/environment-builds/most-recent/{pu}", timeout=60)
            except Exception as ex:
                print("  environment-builds poll error:", str(ex)[:200]); payload = None
            b = _find_build(payload, env_uuid) if payload is not None else None
            if b is None and not shape_known and time.time() - t0 > 2 * ENV_BUILD_POLL:
                print(f"environment-builds response shape unknown ({str(payload)[:200]}) — waiting {ENV_BUILD_BLIND_WAIT // 60} min blindly", flush=True)
                time.sleep(ENV_BUILD_BLIND_WAIT); return
            if b is not None:
                shape_known = True; st = str(b.get("status") or "").upper()
                print(time.strftime("%H:%M:%S"), "environment build:", st or "?", flush=True)
                if st == "SUCCESS": return
                if st in ("FAILURE", "ABORTED"):
                    raise SystemExit(f"environment build {st} for {env_uuid} — veja o log do build na UI (Environments) e rode de novo")
            time.sleep(ENV_BUILD_POLL)
        raise SystemExit(f"environment build não terminou em {ENV_BUILD_TIMEOUT // 60} min — confira a UI e rode de novo com --skip-upload --start")

    def upload(self, pu: str, local: Path, dest_dir: str) -> None:
        d = "/" + dest_dir.strip("/") + "/"; body = local.read_bytes(); last = ""
        for attempt in range(1, UPLOAD_ATTEMPTS + 1):
            r = self.d.raw("POST", f"{self.d.orchest}/async/file-management/upload", params={"root": "/project-dir", "path": d, "project_uuid": pu},
                           files={"file": (local.name, body)}, timeout=600)
            if r.ok: return
            last = f"{r.status_code} {r.text[:300]}"; print(f"  upload {local.name} attempt {attempt}/{UPLOAD_ATTEMPTS} failed: {last}", flush=True)
            time.sleep(3 * attempt)
        raise RuntimeError(f"upload {local} -> {d}: {last}")

    def upload_all(self, pu: str, files: List[Path]) -> None:
        for i, f in enumerate(files, 1):
            rel = f.relative_to(ROOT)  # backend/... ou frontend/dist/...
            self.upload(pu, f, rel.parent.as_posix())
            print(f"  [{i}/{len(files)}] {rel.as_posix()}", flush=True)
        print(f"uploaded {len(files)} files")

    def ensure_pipeline(self, pu: str) -> str:
        pls = {p["name"]: p["uuid"] for p in self.d.orchest_get(f"/async/pipelines/{pu}").get("result", [])}
        for name in (PIPELINE, PIPELINE_TITLE):
            if name in pls: return pls[name]
        r = self.d.orchest_post(f"/async/pipelines/create/{pu}", json={"name": PIPELINE, "pipeline_path": f"{PIPELINE}.orchest"})
        return r.get("pipeline_uuid") or r["uuid"]

    def save_pipeline(self, pu: str, pl: str, doc: dict) -> None:
        r = self.d.raw("PUT", f"{self.d.orchest}/async/pipelines/json/{pu}/{pl}", data={"pipeline_json": json.dumps(doc)}, timeout=120)  # FORM, não JSON
        if not r.ok: raise RuntimeError(f"save pipeline: {r.status_code} {r.text[:300]}")

    def _services(self, X: str, pu: str) -> list:
        r = self.d.raw("GET", X, params={"project_uuid": pu}, timeout=60)
        if not r.ok: raise RuntimeError(f"list standalone services: {r.status_code} {r.text[:300]}")
        return r.json().get("standalone_services", [])

    def start_service(self, pu: str, pl: str) -> dict:
        X = f"{self.d.orchest}/catch/api-proxy/api/standalone-services"
        mine = lambda s: s.get("pipeline_uuid") == pl and s.get("name") == SERVICE
        old = {s["uuid"] for s in self._services(X, pu) if mine(s)}
        for u in old: self.d.raw("DELETE", f"{X}/{u}", timeout=60); print("deleted old service", u)  # sem update: DELETE+create (renova creds AWS, URL estável)
        t0 = time.time()
        while old and time.time() - t0 < 60:
            if not old & {s["uuid"] for s in self._services(X, pu)}: break
            time.sleep(5)
        else:
            if old: print("warning: old services still listed after 60 s, creating anyway")
        r = self.d.raw("POST", X + "/", json={"project_uuid": pu, "pipeline_uuid": pl, "service_type": "user", "name": SERVICE}, timeout=120)
        if not r.ok: raise RuntimeError(f"standalone service: {r.status_code} {r.text[:300]}")
        svc = r.json(); t0 = time.time()
        while time.time() - t0 < 600:
            svc = self.d.raw("GET", f"{X}/{svc['uuid']}", timeout=60).json(); ps = svc.get("pod_status") or {}
            print(time.strftime("%H:%M:%S"), svc.get("status"), ps.get("pod_phase"), ps.get("error_code") or "", flush=True)
            if svc.get("status") in ("RUNNING", "FAILED"): break
            time.sleep(15)
        if svc.get("status") != "RUNNING": raise RuntimeError(f"service did not start: {json.dumps(svc.get('pod_status'))[:800]}")
        self.m["standalone_service_uuid"] = svc["uuid"]; self.m["dataapp_url"] = self.d.orchest + svc["base_url"].rstrip("/") + "/"; return svc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", action="store_true"); ap.add_argument("--skip-upload", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not (OUT / "index.html").exists() and not a.skip_upload:
        raise SystemExit(f"{OUT}/index.html ausente — rode `cd frontend && npm run build`")
    files = upload_files()
    if a.dry_run:
        print(json.dumps(service_doc("PL", "ENV"), indent=1, ensure_ascii=False))
        for f in files: print(" ", f.relative_to(ROOT).as_posix())
        print("files:", len(files)); return
    dp = Deployer(); pu = dp.project(); dp.save()
    if not a.skip_upload: dp.upload_all(pu, files)
    env, created = dp.environment(pu); dp.save()
    if created: dp.wait_environment_build(pu, env)
    pl = dp.ensure_pipeline(pu)
    base_path = f"/pbp-service-{SERVICE}-{pu[:18]}{pl[:18]}_{PORT}"
    dp.m.update({"pipeline_uuid": pl, "base_path": base_path, "dataapp_url": f"{dp.d.orchest}{base_path}/"}); dp.save()
    print("base path =", base_path)
    dp.save_pipeline(pu, pl, service_doc(pl, env))
    if a.start: dp.d.login(); dp.start_service(pu, pl); dp.save()
    print("manifest ->", MANIFEST); print("data app ->", dp.m["dataapp_url"])


if __name__ == "__main__":
    main()
