from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routes.evaluate import router as evaluate_router
from app.routes.pipeline import router as pipeline_router


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
    
    # Inicializa LLM generator se a API key estiver configurada
    import os
    if os.getenv("OPENAI_API_KEY"):
        print("🤖 Inicializando gerador LLM...")
        from app.llm_client import init_llm_generator
        init_llm_generator()
        print("✅ Gerador LLM inicializado!")
    else:
        print("⚠️ OPENAI_API_KEY não configurada - Pipeline de geração desabilitado")
    
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
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["Pipeline"])


def get_evaluator():
    """Retorna a instância do evaluator."""
    return evaluator



