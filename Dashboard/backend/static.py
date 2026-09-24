from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, Response

DEFAULT_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
_HEAD_RE = re.compile(r"<head[^>]*>", re.IGNORECASE)


def base_path() -> str:
    return os.getenv("APP_BASE_PATH", "").rstrip("/")


def _is_api_or_health(full_path: str) -> bool:
    return (
        full_path == "api"
        or full_path.startswith("api/")
        or full_path == "health"
        or full_path.startswith("health/")
    )


def install(app: FastAPI) -> None:
    dist = Path(os.getenv("FRONTEND_DIST", str(DEFAULT_DIST)))
    base = base_path()

    @app.middleware("http")
    async def strip_base(request: Request, call_next):
        path = request.scope["path"]
        if base and (path == base or path.startswith(base + "/")):
            request.scope["path"] = path[len(base):] or "/"
            request.scope["root_path"] = base
        return await call_next(request)

    if not (dist / "index.html").exists():
        return
    index = (dist / "index.html").read_text(encoding="utf-8")
    escaped_href = html.escape(base, quote=True)
    js_base = json.dumps(base)
    inject = f'<base href="{escaped_href}/"><script>window.__APP_BASE__={js_base}</script>'
    index = _HEAD_RE.sub(lambda m: m.group(0) + inject, index, count=1)

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> Response:
        if _is_api_or_health(full_path):
            return Response(status_code=404)
        candidate = (dist / full_path).resolve()
        if full_path and candidate.is_file() and dist.resolve() in candidate.parents:
            return FileResponse(candidate)
        return HTMLResponse(index, headers={"Cache-Control": "no-cache"})
