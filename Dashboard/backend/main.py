import os

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.api.fornecedores import router as fornecedores_router

from backend.api.medicamentos import router as medicamentos_router
from backend.api.compras import router as compras_router
from backend.api.leitos import router as leitos_router
from backend.database import get_connection


app = FastAPI(
    title="Dashboard IC API",
    version="0.2.0",
    description="API de leitura para os dashboards do projeto.",
)


cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


app.include_router(medicamentos_router)
app.include_router(compras_router)
app.include_router(leitos_router)
app.include_router(fornecedores_router)


@app.get("/")
def root():
    return {
        "message": "Dashboard IC API",
        "status": "online",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
    }


@app.get("/health/database")
def database_health():
    """Testa a comunicação da API com o PostgreSQL."""
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS result;")
                result = cursor.fetchone()

        return {
            "status": "ok",
            "database": "connected",
            "result": result["result"] if result else None,
        }

    except (psycopg.Error, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Não foi possível conectar ao PostgreSQL: {exc}",
        ) from exc
