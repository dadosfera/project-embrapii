from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


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



