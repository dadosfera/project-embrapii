from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, Response

DEFAULT_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"


def base_path() -> str:
    return os.getenv("APP_BASE_PATH", "").rstrip("/")


def install(app: FastAPI) -> None:
    dist = Path(os.getenv("FRONTEND_DIST", str(DEFAULT_DIST)))
    base = base_path()

    @app.middleware("http")
    async def strip_base(request: Request, call_next):
        path = request.scope["path"]
        if base and (path == base or path.startswith(base + "/")):
            request.scope["path"] = path[len(base):] or "/"
        return await call_next(request)

    if not (dist / "index.html").exists():
        return
    index = (dist / "index.html").read_text(encoding="utf-8")
    inject = f'<base href="{base}/"><script>window.__APP_BASE__="{base}"</script>'
    index = index.replace("<head>", "<head>" + inject, 1)

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> Response:
        if full_path.startswith(("api/", "health")):
            return Response(status_code=404)
        candidate = (dist / full_path).resolve()
        if full_path and candidate.is_file() and dist.resolve() in candidate.parents:
            return FileResponse(candidate)
        return HTMLResponse(index, headers={"Cache-Control": "no-cache"})
