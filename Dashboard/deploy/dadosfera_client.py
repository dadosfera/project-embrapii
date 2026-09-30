# Dashboard/deploy/dadosfera_client.py (copia de kine-gest-ddf-oic/apps/oic-visitors/deploy/)
"""Dadosfera SSO + Módulo de Inteligência (Orchest) helpers. Source of truth: demo-lakehouse-porto/scripts/maestro_client.py.
`POST maestro/auth/sign-in` returns accessToken + ddf-auth cookies (Domain=.dadosfera.ai) = SSO for app-intelligence-<tenant>."""
from __future__ import annotations
import os, re, time
from pathlib import Path
from typing import Any, Dict, Optional
import requests

MAESTRO = os.getenv("MAESTRO_BASE_URL", "https://maestro.dadosfera.ai")


def load_env(path: Optional[str]) -> Dict[str, str]:
    env: Dict[str, str] = {}
    for cand in [path, ".env", Path(__file__).resolve().parents[1] / ".env"]:
        if cand and Path(cand).exists():
            for line in open(cand):
                m = re.match(r'^\s*([A-Za-z_]\w*)=(.*)$', line.rstrip("\n"))
                if m: env.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
    return env


class Dadosfera:
    def __init__(self) -> None:
        env = load_env(os.getenv("DADOSFERA_ENV_FILE"))
        g = lambda k, d=None: os.getenv(k) or env.get(k) or d
        self.username = g("DADOSFERA_USERNAME") or g("DADOSFERADEMO_USER"); self.password = g("DADOSFERA_PASSWORD") or g("DADOSFERADEMO_PASSWORD")
        if not self.username or not self.password: raise SystemExit("missing DADOSFERA_USERNAME/DADOSFERA_PASSWORD (or DADOSFERADEMO_USER/PASSWORD) in .env")
        self.customer = g("DADOSFERA_CUSTOMER_NAME", "dadosferademo")
        self.orchest = g("ORCHEST_BASE_URL", f"https://app-intelligence-{self.customer}2.dadosfera.ai")
        self.s = requests.Session(); self.s.headers["Accept"] = "application/json"; self._exp = 0.0

    def login(self) -> None:
        r = self.s.post(f"{MAESTRO}/auth/sign-in", json={"username": self.username, "password": self.password}, timeout=30); r.raise_for_status()
        self.s.headers["Authorization"] = r.json()["tokens"]["accessToken"]; self._exp = time.time() + 25 * 60  # Maestro: bare token; ddf-* cookies stay in the session (tenant SSO)

    def raw(self, method: str, url: str, **kw: Any) -> requests.Response:
        """Ensure login, send, and retry once on 401 (re-login). Returns the Response without raising on status.
        File uploads: pass `files` with bytes (not an open stream) so the retry can re-send the body."""
        if time.time() > self._exp: self.login()
        timeout = kw.pop("timeout", 120)
        r = self.s.request(method, url, timeout=timeout, **kw)
        if r.status_code == 401: self.login(); r = self.s.request(method, url, timeout=timeout, **kw)
        return r

    def req(self, method: str, url: str, **kw: Any) -> Any:
        r = self.raw(method, url, **kw)
        if not r.ok: raise RuntimeError(f"{method} {url} -> {r.status_code}: {r.text[:500]}")
        if "json" not in r.headers.get("content-type", ""): raise RuntimeError(f"{method} {url} returned non-JSON (no SSO?)")
        return r.json() if r.content else {}

    def orchest_get(self, path: str, **kw: Any) -> Any: return self.req("GET", f"{self.orchest}{path}", **kw)
    def orchest_post(self, path: str, **kw: Any) -> Any: return self.req("POST", f"{self.orchest}{path}", **kw)
