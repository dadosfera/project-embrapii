from sentence_transformers import SentenceTransformer, CrossEncoder
from sacrebleu.metrics import BLEU
import numpy as np
from typing import List, Dict, Any


class ParaphraseEvaluator:
    """
    Avaliador de qualidade de paráfrases usando três métricas:
    - Cross-Encoder: Similaridade semântica profunda (0-1)
    - SBERT: Similaridade de embeddings via cosine (0-1)
    - BLEU: Sobreposição de n-gramas (0-100, menor = mais diverso)
    """

    def __init__(self):
        """Inicializa os modelos de avaliação."""
        # Modelo SBERT multilingual para embeddings
        self.sbert_model = SentenceTransformer(
            'paraphrase-multilingual-MiniLM-L12-v2'
        )
        
        # Cross-Encoder para similaridade semântica
        self.cross_encoder = CrossEncoder(
            'cross-encoder/stsb-roberta-base'
        )
        
        # BLEU para diversidade lexical
        self.bleu = BLEU(effective_order=True)

    def _compute_cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calcula similaridade de cosseno entre dois embeddings."""
        dot_product = np.dot(emb1, emb2)
        norm_product = np.linalg.norm(emb1) * np.linalg.norm(emb2)
        return float(dot_product / norm_product) if norm_product > 0 else 0.0

    def evaluate_pair(self, original: str, paraphrase: str) -> Dict[str, float]:
        """
        Avalia um único par (original, paráfrase).
        
        Args:
            original: Texto original
            paraphrase: Paráfrase do texto original
            
        Returns:
            Dict com scores de cross_encoder, sbert e bleu
        """
        # Cross-Encoder (retorna valor entre -1 e 1, normalizamos para 0-1)
        ce_raw = self.cross_encoder.predict([(original, paraphrase)])[0]
        ce_score = (ce_raw + 1) / 2  # Normaliza para 0-1
        
        # SBERT - Cosine Similarity
        emb_original = self.sbert_model.encode(original)
        emb_paraphrase = self.sbert_model.encode(paraphrase)
        sbert_score = self._compute_cosine_similarity(emb_original, emb_paraphrase)
        
        # BLEU Score (0-100)
        bleu_result = self.bleu.sentence_score(
            hypothesis=paraphrase,
            references=[original]
        )
        bleu_score = bleu_result.score
        
        return {
            "cross_encoder": round(ce_score, 4),
            "sbert": round(sbert_score, 4),
            "bleu": round(bleu_score, 2)
        }

    def evaluate_batch(self, pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Avalia um batch de pares.
        
        Args:
            pairs: Lista de dicts com 'original' e 'paraphrase'
            
        Returns:
            Dict com 'results' (lista de scores) e 'summary' (médias)
        """
        results = []
        
        for pair in pairs:
            scores = self.evaluate_pair(pair["original"], pair["paraphrase"])
            results.append({
                "original": pair["original"],
                "paraphrase": pair["paraphrase"],
                **scores
            })
        
        # Calcula médias
        if results:
            summary = {
                "cross_encoder_avg": round(
                    np.mean([r["cross_encoder"] for r in results]), 4
                ),
                "sbert_avg": round(
                    np.mean([r["sbert"] for r in results]), 4
                ),
                "bleu_avg": round(
                    np.mean([r["bleu"] for r in results]), 2
                ),
                "total_pairs": len(results)
            }
        else:
            summary = {
                "cross_encoder_avg": 0.0,
                "sbert_avg": 0.0,
                "bleu_avg": 0.0,
                "total_pairs": 0
            }
        
        return {
            "results": results,
            "summary": summary
        }



