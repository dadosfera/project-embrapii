from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class PipelineSession(Base):
    """Modelo para armazenar sessões do pipeline de geração."""
    
    __tablename__ = "pipeline_sessions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    current_step = Column(Integer, default=1)  # 1-6
    
    # Schema do banco de dados (DDL)
    schema = Column(Text, nullable=False)
    
    # Dados de cada etapa em JSON
    questions_data = Column(JSON, default=list)  # Lista de QuestionItem
    sql_pairs_data = Column(JSON, default=list)  # Lista de SQLPairItem
    paraphrases_data = Column(JSON, default=list)  # Lista de ParaphraseItem
    
    # Métricas finais (após avaliação)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=True)
    
    # Relacionamento com a avaliação
    evaluation = relationship("Evaluation", backref="pipeline_session")


class Evaluation(Base):
    """Modelo para armazenar uma avaliação (batch de pares)."""
    
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_pairs = Column(Integer, nullable=False)
    cross_encoder_avg = Column(Float, nullable=False)
    sbert_avg = Column(Float, nullable=False)
    bleu_avg = Column(Float, nullable=False)
    
    # Relacionamento com os pares
    pairs = relationship("EvaluationPair", back_populates="evaluation", cascade="all, delete-orphan")


class EvaluationPair(Base):
    """Modelo para armazenar cada par avaliado."""
    
    __tablename__ = "evaluation_pairs"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False)
    original = Column(Text, nullable=False)
    paraphrase = Column(Text, nullable=False)
    cross_encoder = Column(Float, nullable=False)
    sbert = Column(Float, nullable=False)
    bleu = Column(Float, nullable=False)
    
    # Relacionamento com a avaliação
    evaluation = relationship("Evaluation", back_populates="pairs")



