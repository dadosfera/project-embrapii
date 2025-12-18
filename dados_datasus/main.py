from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.rotas import rotas
from app.database.duckDB_system import db_instance
import uvicorn
 
# --- CICLO DE VIDA ---
# Isso garante que conectamos ao banco quando o servidor liga
# e desconectamos quando ele desliga.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que roda ao iniciar
    try:
        db_instance.get_connection()
    except Exception as e:
        print(f"AVISO: Não foi possível conectar ao Banco: {e}")
    
    yield # O servidor roda aqui
    
    # Código que roda ao desligar
    db_instance.close()

app = FastAPI(
    title="API DataSUS via FastAPI",
    description="API DuckDB portada para servidor",
    version="2.0.0",
    lifespan=lifespan
)

# Inclui as rotas
app.include_router(rotas.router)

@app.get("/")
def root():
    return {"status": "online", "env": "Production Linux Server"}

# Se for rodar via 'python main.py'
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)