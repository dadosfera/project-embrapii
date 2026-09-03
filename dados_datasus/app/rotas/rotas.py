from fastapi import APIRouter, HTTPException, Query
from app.database.duckDB_system import db_instance
import pandas as pd

router = APIRouter(
    prefix="/rotas",
    tags=["Consultas DuckDB"]
)

@router.get("/tabelas")
async def listar_tabelas():
    """Retorna a lista de tabelas existentes no arquivo DuckDB."""
    try:
        # Usamos nossa instância criada no outro arquivo
        df = db_instance.execute_query_df("SHOW TABLES;")
        tabelas = df["name"].tolist()
        return {"tabelas_disponiveis": tabelas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/query")
async def executar_query(
    sql: str = Query(..., description="Query SQL ANSI para execução.")
):
    """
    Executa SQL arbitrário.
    CUIDADO: Em produção, validar input para evitar SQL Injection destrutivo,
    embora o banco esteja em read_only=True.
    """
    try:
        # Limita a query para evitar travamento do servidor (opcional)
        if "limit" not in sql.lower() and "count" not in sql.lower():
            sql += " LIMIT 100"

        df = db_instance.execute_query_df(sql)
        
        # Converte para dicionário (JSON friendly)
        # O replace({float('nan'): None}) trata valores nulos do Pandas que quebram o JSON
        dados = df.where(pd.notnull(df), None).to_dict(orient="records")

        return {
            "linhas_retornadas": len(dados),
            "resultado": dados
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na query: {str(e)}")

