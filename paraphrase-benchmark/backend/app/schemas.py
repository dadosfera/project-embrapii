from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# === Request Schemas ===

class ParaphrasePair(BaseModel):
    """Par de texto original e paráfrase para avaliação."""
    original: str
    paraphrase: str


class EvaluationRequest(BaseModel):
    """Request para avaliar múltiplos pares."""
    pairs: List[ParaphrasePair]


# === Response Schemas ===

class MetricResult(BaseModel):
    """Resultado das métricas para um par."""
    original: str
    paraphrase: str
    cross_encoder: float
    sbert: float
    bleu: float


class EvaluationSummary(BaseModel):
    """Resumo estatístico da avaliação."""
    cross_encoder_avg: float
    sbert_avg: float
    bleu_avg: float
    total_pairs: int


class EvaluationResponse(BaseModel):
    """Response completa de uma avaliação."""
    id: int
    created_at: datetime
    summary: EvaluationSummary
    results: List[MetricResult]

    class Config:
        from_attributes = True


class EvaluationListItem(BaseModel):
    """Item resumido para listagem do histórico."""
    id: int
    created_at: datetime
    total_pairs: int
    cross_encoder_avg: float
    sbert_avg: float
    bleu_avg: float

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Response do health check."""
    status: str
    models_loaded: bool
    database_connected: bool



