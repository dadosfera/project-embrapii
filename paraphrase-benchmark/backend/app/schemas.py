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


# === Pipeline Schemas ===

class QuestionItem(BaseModel):
    """Uma pergunta gerada com metadados."""
    nl_query: str
    complexity: str  # simple, medium, complex
    query_type: str  # filter, aggregation, join, subquery, window
    tables_involved: List[str]
    description: str
    selected: bool = True  # Para curadoria


class GenerateQuestionsRequest(BaseModel):
    """Request para gerar perguntas a partir do schema."""
    schema: str
    num_questions: int = 50
    context: Optional[str] = None


class GenerateQuestionsResponse(BaseModel):
    """Response com perguntas geradas."""
    session_id: int
    questions: List[QuestionItem]
    total_generated: int


class SQLPairItem(BaseModel):
    """Par pergunta + SQL gerado."""
    nl_query: str
    sql_query: str
    complexity: str
    query_type: str
    tables_involved: List[str]
    description: str
    sql_explanation: Optional[str] = None


class GenerateSQLRequest(BaseModel):
    """Request para gerar SQLs para perguntas curadas."""
    session_id: int
    schema: str
    questions: List[QuestionItem]


class GenerateSQLResponse(BaseModel):
    """Response com pares NL-SQL."""
    session_id: int
    pairs: List[SQLPairItem]
    total_pairs: int


class ParaphraseItem(BaseModel):
    """Par com paráfrase."""
    nl_query: str
    sql_query: str
    original_nl_query: str
    is_original: bool
    complexity: str
    query_type: str
    tables_involved: List[str]


class GenerateParaphrasesRequest(BaseModel):
    """Request para gerar paráfrases."""
    session_id: int
    pairs: List[SQLPairItem]
    num_paraphrases: int = 5


class GenerateParaphrasesResponse(BaseModel):
    """Response com paráfrases geradas."""
    session_id: int
    paraphrases: List[ParaphraseItem]
    total_original: int
    total_paraphrases: int


class RegenerateSQLRequest(BaseModel):
    """Request para regenerar SQLs das paráfrases."""
    session_id: int
    schema: str
    paraphrases: List[ParaphraseItem]


class RegenerateSQLResponse(BaseModel):
    """Response com SQLs regenerados."""
    session_id: int
    pairs: List[ParaphraseItem]
    total_pairs: int


class PipelineSessionCreate(BaseModel):
    """Request para criar/salvar sessão do pipeline."""
    schema: str
    questions: Optional[List[QuestionItem]] = None
    sql_pairs: Optional[List[SQLPairItem]] = None
    paraphrases: Optional[List[ParaphraseItem]] = None
    current_step: int = 1


class PipelineSessionResponse(BaseModel):
    """Response com dados da sessão."""
    id: int
    created_at: datetime
    updated_at: datetime
    current_step: int
    schema: str
    total_questions: int
    total_sql_pairs: int
    total_paraphrases: int

    class Config:
        from_attributes = True


class PipelineSessionDetail(BaseModel):
    """Detalhes completos de uma sessão."""
    id: int
    created_at: datetime
    updated_at: datetime
    current_step: int
    schema: str
    questions: List[QuestionItem]
    sql_pairs: List[SQLPairItem]
    paraphrases: List[ParaphraseItem]

    class Config:
        from_attributes = True

