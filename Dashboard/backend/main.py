import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.api.fornecedores import router as fornecedores_router

from backend.api.medicamentos import router as medicamentos_router
from backend.api.compras import router as compras_router
from backend.api.leitos import router as leitos_router
from backend.database import DatabaseError, Q, fetch_one, get_engine


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
    """Testa a comunicação da API com o banco do engine ativo."""
    engine = get_engine()
    try:
        row = fetch_one(Q(pg="SELECT 1 AS result", sf="SELECT 1 AS result"))
        return {"status": "ok", "engine": engine, "result": row["result"] if row else None}
    except (DatabaseError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=f"Banco indisponível ({engine}): {exc}") from exc


from backend import static  # noqa: E402

static.install(app)
