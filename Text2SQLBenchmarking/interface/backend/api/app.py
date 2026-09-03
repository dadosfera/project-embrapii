"""Factory FastAPI da Fase 7; cada app possui um container próprio."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .dependencies import ApiContainer
from .errors import install_error_handlers
from .routes import benchmark, catalog, chat, health, status


def create_app(*, container: ApiContainer | None = None) -> FastAPI:
    owned_container = container

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        active_container = owned_container or ApiContainer.create()
        app.state.container = active_container
        active_container.benchmark.reconcile_incomplete_jobs()
        try:
            yield
        finally:
            if active_container.chat_executor is not None:
                active_container.chat_executor.shutdown()
            active_container.benchmark_executor.shutdown()
            active_container.operations.shutdown()

    app = FastAPI(title="Text2SQL Benchmark Interface API", version="v1", lifespan=lifespan)
    install_error_handlers(app)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(catalog.router, prefix="/api/v1")
    app.include_router(status.router, prefix="/api/v1")
    app.include_router(benchmark.router, prefix="/api/v1")
    app.include_router(benchmark.status_router, prefix="/api/v1")
    app.include_router(benchmark.intent_router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    return app
