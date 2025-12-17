from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Evaluation, EvaluationPair
from app.schemas import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationListItem,
    EvaluationSummary,
    MetricResult,
    HealthResponse
)

router = APIRouter()


def get_evaluator():
    """Obtém o evaluator do módulo main."""
    from app.main import get_evaluator as _get_evaluator
    return _get_evaluator()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Verifica se a API está funcionando e os modelos estão carregados.
    """
    from sqlalchemy import text
    
    evaluator = get_evaluator()
    
    # Testa conexão com banco
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False
    
    return HealthResponse(
        status="healthy" if evaluator and db_connected else "unhealthy",
        models_loaded=evaluator is not None,
        database_connected=db_connected
    )


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_paraphrases(
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Avalia um conjunto de pares (original, paráfrase) e salva no histórico.
    
    - **pairs**: Lista de pares contendo 'original' e 'paraphrase'
    
    Retorna métricas individuais e médias agregadas.
    """
    evaluator = get_evaluator()
    
    if evaluator is None:
        raise HTTPException(
            status_code=503,
            detail="Modelos de avaliação não carregados"
        )
    
    if not request.pairs:
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer pelo menos um par para avaliação"
        )
    
    # Converte para formato esperado pelo evaluator
    pairs_data = [
        {"original": p.original, "paraphrase": p.paraphrase}
        for p in request.pairs
    ]
    
    # Executa avaliação
    evaluation_result = evaluator.evaluate_batch(pairs_data)
    
    # Salva no banco
    db_evaluation = Evaluation(
        total_pairs=evaluation_result["summary"]["total_pairs"],
        cross_encoder_avg=evaluation_result["summary"]["cross_encoder_avg"],
        sbert_avg=evaluation_result["summary"]["sbert_avg"],
        bleu_avg=evaluation_result["summary"]["bleu_avg"]
    )
    db.add(db_evaluation)
    db.flush()  # Obtém o ID antes do commit
    
    # Salva os pares individuais
    for result in evaluation_result["results"]:
        db_pair = EvaluationPair(
            evaluation_id=db_evaluation.id,
            original=result["original"],
            paraphrase=result["paraphrase"],
            cross_encoder=result["cross_encoder"],
            sbert=result["sbert"],
            bleu=result["bleu"]
        )
        db.add(db_pair)
    
    db.commit()
    db.refresh(db_evaluation)
    
    # Monta response
    return EvaluationResponse(
        id=db_evaluation.id,
        created_at=db_evaluation.created_at,
        summary=EvaluationSummary(
            cross_encoder_avg=db_evaluation.cross_encoder_avg,
            sbert_avg=db_evaluation.sbert_avg,
            bleu_avg=db_evaluation.bleu_avg,
            total_pairs=db_evaluation.total_pairs
        ),
        results=[
            MetricResult(
                original=r["original"],
                paraphrase=r["paraphrase"],
                cross_encoder=r["cross_encoder"],
                sbert=r["sbert"],
                bleu=r["bleu"]
            )
            for r in evaluation_result["results"]
        ]
    )


@router.get("/history", response_model=List[EvaluationListItem])
async def list_evaluations(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Lista o histórico de avaliações.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros (padrão: 50)
    """
    evaluations = (
        db.query(Evaluation)
        .order_by(Evaluation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        EvaluationListItem(
            id=e.id,
            created_at=e.created_at,
            total_pairs=e.total_pairs,
            cross_encoder_avg=e.cross_encoder_avg,
            sbert_avg=e.sbert_avg,
            bleu_avg=e.bleu_avg
        )
        for e in evaluations
    ]


@router.get("/history/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém detalhes de uma avaliação específica, incluindo todos os pares.
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail=f"Avaliação {evaluation_id} não encontrada"
        )
    
    return EvaluationResponse(
        id=evaluation.id,
        created_at=evaluation.created_at,
        summary=EvaluationSummary(
            cross_encoder_avg=evaluation.cross_encoder_avg,
            sbert_avg=evaluation.sbert_avg,
            bleu_avg=evaluation.bleu_avg,
            total_pairs=evaluation.total_pairs
        ),
        results=[
            MetricResult(
                original=p.original,
                paraphrase=p.paraphrase,
                cross_encoder=p.cross_encoder,
                sbert=p.sbert,
                bleu=p.bleu
            )
            for p in evaluation.pairs
        ]
    )


@router.delete("/history/{evaluation_id}")
async def delete_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove uma avaliação do histórico.
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail=f"Avaliação {evaluation_id} não encontrada"
        )
    
    db.delete(evaluation)
    db.commit()
    
    return {"message": f"Avaliação {evaluation_id} removida com sucesso"}

