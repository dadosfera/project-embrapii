#!/usr/bin/env python3
"""Gera um storageState do Playwright com os cookies de SSO da Dadosfera (ddf-*, Domain=.dadosfera.ai).
Uso: DADOSFERA_ENV_FILE=... python3 deploy/sso_storage_state.py /caminho/fora-do-repo/state.json
     cd frontend && E2E_STORAGE_STATE=/caminho/fora-do-repo/state.json E2E_BASE_URL=<dataapp_url> npx playwright test
O arquivo carrega token de sessão: grave fora do repositório e apague depois."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dadosfera_client import Dadosfera  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("uso: sso_storage_state.py <saida.json>")
    out = Path(sys.argv[1]).expanduser().resolve()
    repo = Path(__file__).resolve().parents[2]  # raiz do repositório (project-embrapii)
    if out == repo or repo in out.parents:
        raise SystemExit(f"recusado: {out} fica dentro do repositório ({repo}); grave fora dele")
    d = Dadosfera(); d.login()
    cookies = [{"name": c.name, "value": c.value, "domain": c.domain or ".dadosfera.ai", "path": c.path or "/",
                "expires": float(c.expires) if c.expires else -1, "httpOnly": bool(c.has_nonstandard_attr("HttpOnly")),
                "secure": bool(c.secure), "sameSite": "Lax"} for c in d.s.cookies]
    if out.exists(): out.unlink()
    fd = os.open(str(out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)  # nasce 0600, sem janela legível
    with os.fdopen(fd, "w") as fh:
        json.dump({"cookies": cookies, "origins": []}, fh)
    print(f"{len(cookies)} cookies -> {out} ({', '.join(sorted({c['name'] for c in cookies}))})")


if __name__ == "__main__":
    main()
