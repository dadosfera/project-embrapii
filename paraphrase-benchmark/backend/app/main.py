from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routes.evaluate import router as evaluate_router


# Variável global para o evaluator (carregado no startup)
evaluator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    global evaluator
    
    # Startup
    print("🚀 Iniciando aplicação...")
    
    # Inicializa banco de dados
    print("📦 Inicializando banco de dados...")
    init_db()
    
    # Carrega modelos de avaliação
    print("🤖 Carregando modelos de avaliação...")
    from app.evaluator import ParaphraseEvaluator
    evaluator = ParaphraseEvaluator()
    print("✅ Modelos carregados com sucesso!")
    
    yield
    
    # Shutdown
    print("👋 Encerrando aplicação...")


app = FastAPI(
    title="Paraphrase Benchmark API",
    description="API para avaliar qualidade de paráfrases usando BLEU, SBERT e Cross-Encoder",
    version="1.0.0",
    lifespan=lifespan
)

# Configuração CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra rotas
app.include_router(evaluate_router, prefix="/api", tags=["Evaluation"])


def get_evaluator():
    """Retorna a instância do evaluator."""
    return evaluator



