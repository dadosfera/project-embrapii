"""Rotas para o pipeline de geração NL-SQL."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os

from app.database import get_db
from app.models import PipelineSession
from app.schemas import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    GenerateSQLRequest,
    GenerateSQLResponse,
    GenerateParaphrasesRequest,
    GenerateParaphrasesResponse,
    RegenerateSQLRequest,
    RegenerateSQLResponse,
    PipelineSessionCreate,
    PipelineSessionResponse,
    PipelineSessionDetail,
    QuestionItem,
    SQLPairItem,
    ParaphraseItem
)

router = APIRouter()


def get_llm_generator():
    """Obtém o gerador LLM."""
    from app.llm_client import get_llm_generator as _get_llm_generator
    return _get_llm_generator()


def check_any_llm_configured():
    """Verifica se alguma API Key de LLM está configurada."""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    if not any([openai_key, anthropic_key, google_key]):
        raise HTTPException(
            status_code=503,
            detail="Nenhuma API Key configurada. Configure OPENAI_API_KEY, ANTHROPIC_API_KEY ou GOOGLE_API_KEY."
        )


@router.get("/providers")
async def list_providers():
    """Lista provedores de LLM disponíveis."""
    from app.llm_client import get_available_providers, get_llm_generator
    
    providers = get_available_providers()
    
    # Tenta obter info do modelo atual
    current_model = None
    try:
        generator = get_llm_generator()
        current_model = generator.get_model_info()
    except:
        pass
    
    return {
        "providers": providers,
        "current": current_model
    }


@router.post("/set-provider")
async def set_provider(provider: str, model: str = None):
    """Define o provedor e modelo de LLM."""
    from app.llm_client import set_llm_provider, PROVIDERS
    
    if provider not in PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Provedor '{provider}' não suportado. Use: {list(PROVIDERS.keys())}"
        )
    
    env_key = PROVIDERS[provider]["env_key"]
    if not os.getenv(env_key):
        raise HTTPException(
            status_code=503,
            detail=f"{env_key} não configurada para o provedor '{provider}'"
        )
    
    try:
        info = set_llm_provider(provider, model)
        return {"success": True, "model_info": info}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao configurar provedor: {str(e)}"
        )


# Mantém compatibilidade
def check_openai_configured():
    """Verifica se a API Key da OpenAI está configurada."""
    check_any_llm_configured()


@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db)
):
    """
    Gera perguntas em linguagem natural baseadas no schema do banco.
    
    - **schema**: DDL ou descrição do schema do banco de dados
    - **num_questions**: Número aproximado de perguntas a gerar (padrão: 50)
    - **context**: Contexto adicional sobre o domínio dos dados
    """
    check_openai_configured()
    
    if not request.schema.strip():
        raise HTTPException(
            status_code=400,
            detail="O schema do banco de dados é obrigatório"
        )
    
    # Cria sessão do pipeline
    session = PipelineSession(
        schema=request.schema,
        current_step=1,
        questions_data=[],
        sql_pairs_data=[],
        paraphrases_data=[]
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    try:
        generator = get_llm_generator()
        questions = await generator.generate_questions(
            schema=request.schema,
            num_questions=request.num_questions,
            context=request.context
        )
        
        # Adiciona flag selected=True para todas
        questions_with_selection = [
            {**q, "selected": True} for q in questions
        ]
        
        # Atualiza sessão com as perguntas
        session.questions_data = questions_with_selection
        session.current_step = 2
        db.commit()
        
        return GenerateQuestionsResponse(
            session_id=session.id,
            questions=[QuestionItem(**q) for q in questions_with_selection],
            total_generated=len(questions_with_selection)
        )
        
    except Exception as e:
        # Em caso de erro, remove a sessão
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar perguntas: {str(e)}"
        )


@router.post("/generate-sql", response_model=GenerateSQLResponse)
async def generate_sql(
    request: GenerateSQLRequest,
    db: Session = Depends(get_db)
):
    """
    Gera consultas SQL para as perguntas curadas.
    
    - **session_id**: ID da sessão do pipeline
    - **schema**: Schema do banco de dados
    - **questions**: Lista de perguntas selecionadas na curadoria
    """
    check_openai_configured()
    
    # Busca sessão
    session = db.query(PipelineSession).filter(
        PipelineSession.id == request.session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Sessão {request.session_id} não encontrada"
        )
    
    if not request.questions:
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer pelo menos uma pergunta"
        )
    
    try:
        generator = get_llm_generator()
        
        # Converte para formato esperado
        questions_data = [q.model_dump() for q in request.questions]
        
        sql_pairs = await generator.generate_sql(
            schema=request.schema,
            questions=questions_data
        )
        
        # Atualiza sessão
        session.sql_pairs_data = sql_pairs
        session.current_step = 3
        db.commit()
        
        return GenerateSQLResponse(
            session_id=session.id,
            pairs=[SQLPairItem(**p) for p in sql_pairs],
            total_pairs=len(sql_pairs)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar SQLs: {str(e)}"
        )


@router.post("/generate-paraphrases", response_model=GenerateParaphrasesResponse)
async def generate_paraphrases(
    request: GenerateParaphrasesRequest,
    db: Session = Depends(get_db)
):
    """
    Gera paráfrases para as perguntas originais.
    
    - **session_id**: ID da sessão do pipeline
    - **pairs**: Lista de pares (pergunta, SQL)
    - **num_paraphrases**: Número de paráfrases por pergunta (padrão: 5)
    """
    check_openai_configured()
    
    session = db.query(PipelineSession).filter(
        PipelineSession.id == request.session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Sessão {request.session_id} não encontrada"
        )
    
    if not request.pairs:
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer pelo menos um par"
        )
    
    try:
        generator = get_llm_generator()
        
        pairs_data = [p.model_dump() for p in request.pairs]
        
        paraphrases = await generator.generate_paraphrases(
            pairs=pairs_data,
            num_paraphrases=request.num_paraphrases
        )
        
        # Conta originais e paráfrases
        total_original = len([p for p in paraphrases if p.get("is_original", False)])
        total_paraphrases = len(paraphrases) - total_original
        
        # Atualiza sessão
        session.paraphrases_data = paraphrases
        session.current_step = 4
        db.commit()
        
        return GenerateParaphrasesResponse(
            session_id=session.id,
            paraphrases=[ParaphraseItem(**p) for p in paraphrases],
            total_original=total_original,
            total_paraphrases=total_paraphrases
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar paráfrases: {str(e)}"
        )


@router.post("/regenerate-sql", response_model=RegenerateSQLResponse)
async def regenerate_sql(
    request: RegenerateSQLRequest,
    db: Session = Depends(get_db)
):
    """
    Regenera SQLs para as paráfrases, garantindo consistência.
    
    - **session_id**: ID da sessão do pipeline
    - **schema**: Schema do banco de dados
    - **paraphrases**: Lista de paráfrases para regenerar SQL
    """
    check_openai_configured()
    
    session = db.query(PipelineSession).filter(
        PipelineSession.id == request.session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Sessão {request.session_id} não encontrada"
        )
    
    if not request.paraphrases:
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer as paráfrases"
        )
    
    try:
        generator = get_llm_generator()
        
        paraphrases_data = [p.model_dump() for p in request.paraphrases]
        
        updated_pairs = await generator.regenerate_sql_for_paraphrases(
            schema=request.schema,
            paraphrase_pairs=paraphrases_data
        )
        
        # Atualiza sessão
        session.paraphrases_data = updated_pairs
        session.current_step = 5
        db.commit()
        
        return RegenerateSQLResponse(
            session_id=session.id,
            pairs=[ParaphraseItem(**p) for p in updated_pairs],
            total_pairs=len(updated_pairs)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao regenerar SQLs: {str(e)}"
        )


@router.post("/sessions", response_model=PipelineSessionResponse)
async def save_session(
    request: PipelineSessionCreate,
    db: Session = Depends(get_db)
):
    """
    Cria ou atualiza uma sessão do pipeline.
    """
    session = PipelineSession(
        schema=request.schema,
        current_step=request.current_step,
        questions_data=[q.model_dump() for q in request.questions] if request.questions else [],
        sql_pairs_data=[p.model_dump() for p in request.sql_pairs] if request.sql_pairs else [],
        paraphrases_data=[p.model_dump() for p in request.paraphrases] if request.paraphrases else []
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return PipelineSessionResponse(
        id=session.id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        current_step=session.current_step,
        schema=session.schema,
        total_questions=len(session.questions_data or []),
        total_sql_pairs=len(session.sql_pairs_data or []),
        total_paraphrases=len(session.paraphrases_data or [])
    )


@router.get("/sessions", response_model=List[PipelineSessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Lista todas as sessões do pipeline.
    """
    sessions = (
        db.query(PipelineSession)
        .order_by(PipelineSession.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        PipelineSessionResponse(
            id=s.id,
            created_at=s.created_at,
            updated_at=s.updated_at,
            current_step=s.current_step,
            schema=s.schema,
            total_questions=len(s.questions_data or []),
            total_sql_pairs=len(s.sql_pairs_data or []),
            total_paraphrases=len(s.paraphrases_data or [])
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=PipelineSessionDetail)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém detalhes completos de uma sessão do pipeline.
    """
    session = db.query(PipelineSession).filter(
        PipelineSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Sessão {session_id} não encontrada"
        )
    
    return PipelineSessionDetail(
        id=session.id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        current_step=session.current_step,
        schema=session.schema,
        questions=[QuestionItem(**q) for q in (session.questions_data or [])],
        sql_pairs=[SQLPairItem(**p) for p in (session.sql_pairs_data or [])],
        paraphrases=[ParaphraseItem(**p) for p in (session.paraphrases_data or [])]
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove uma sessão do pipeline.
    """
    session = db.query(PipelineSession).filter(
        PipelineSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Sessão {session_id} não encontrada"
        )
    
    db.delete(session)
    db.commit()
    
    return {"message": f"Sessão {session_id} removida com sucesso"}


@router.put("/sessions/{session_id}/step", response_model=PipelineSessionResponse)
async def update_session_step(
    session_id: int,
    step: int,
    db: Session = Depends(get_db)
):
    """
    Atualiza o step atual da sessão.
    """
    if step < 1 or step > 6:
        raise HTTPException(
            status_code=400,
            detail="Step deve estar entre 1 e 6"
        )
    
    session = db.query(PipelineSession).filter(
        PipelineSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Sessão {session_id} não encontrada"
        )
    
    session.current_step = step
    db.commit()
    db.refresh(session)
    
    return PipelineSessionResponse(
        id=session.id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        current_step=session.current_step,
        schema=session.schema,
        total_questions=len(session.questions_data or []),
        total_sql_pairs=len(session.sql_pairs_data or []),
        total_paraphrases=len(session.paraphrases_data or [])
    )

