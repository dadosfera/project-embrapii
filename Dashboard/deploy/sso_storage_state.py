#!/usr/bin/env python3
"""Gera um storageState do Playwright com os cookies de SSO da Dadosfera (ddf-*, Domain=.dadosfera.ai).
Uso: DADOSFERA_ENV_FILE=... python3 deploy/sso_storage_state.py /caminho/fora-do-repo/state.json
     cd frontend && E2E_STORAGE_STATE=/caminho/fora-do-repo/state.json E2E_BASE_URL=<dataapp_url> npx playwright test
O arquivo carrega token de sessão: grave fora do repositório e apague depois."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dadosfera_client import Dadosfera  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("uso: sso_storage_state.py <saida.json>")
    d = Dadosfera(); d.login()
    cookies = [{"name": c.name, "value": c.value, "domain": c.domain or ".dadosfera.ai", "path": c.path or "/",
                "expires": float(c.expires) if c.expires else -1, "httpOnly": bool(c.has_nonstandard_attr("HttpOnly")),
                "secure": bool(c.secure), "sameSite": "Lax"} for c in d.s.cookies]
    out = Path(sys.argv[1]); out.write_text(json.dumps({"cookies": cookies, "origins": []}))
    out.chmod(0o600)
    print(f"{len(cookies)} cookies -> {out} ({', '.join(sorted({c['name'] for c in cookies}))})")


if __name__ == "__main__":
    main()
