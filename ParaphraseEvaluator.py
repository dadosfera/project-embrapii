from sentence_transformers import SentenceTransformer, CrossEncoder, util
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rich.console import Console
from rich.table import Table
from collections import defaultdict
import numpy as np
from typing import List, Tuple, Dict

class ParaphraseEvaluator:
    def __init__(self, cross_encoder_model: str = "cross-encoder/stsb-roberta-base",
                 sbert_model: str = "all-MiniLM-L6-v2"):
        self.cross_model = CrossEncoder(cross_encoder_model)
        self.sbert_model = SentenceTransformer(sbert_model)
        self.smoothing = SmoothingFunction().method4
        self.console = Console()

    def evaluate_cross_encoder(self, pairs: List[Tuple[str, str]]) -> np.ndarray:
        return self.cross_model.predict(pairs)

    def evaluate_sbert(self, pairs: List[Tuple[str, str]]) -> np.ndarray:
        originals = [pair[0] for pair in pairs]
        paraphrases = [pair[1] for pair in pairs]

        original_embeddings = self.sbert_model.encode(originals, convert_to_tensor=True)
        paraphrase_embeddings = self.sbert_model.encode(paraphrases, convert_to_tensor=True)

        return util.cos_sim(original_embeddings, paraphrase_embeddings).diagonal().cpu().numpy()

    def evaluate_bleu(self, pairs: List[Tuple[str, str]]) -> List[float]:
        return [sentence_bleu([a.split()], b.split(), smoothing_function=self.smoothing)
                for a, b in pairs]

    def _group_by_original(self, pairs: List[Tuple[str, str]], scores: np.ndarray) -> Dict[str, List[float]]:
        grouped = defaultdict(list)
        for (original, _), score in zip(pairs, scores):
            grouped[original].append(score)
        return grouped

    def print_grouped_table(self, title: str, grouped_scores: Dict[str, List[float]]):
        table = Table(title=title, show_lines=True)
        table.add_column("ID", justify="center", style="white")
        table.add_column("N Paráfrases", justify="center", style="orchid")
        table.add_column("Média", justify="right", style="yellow")
        table.add_column("Mediana", justify="right", style="green")

        for idx, (original, scores) in enumerate(grouped_scores.items(), 1):
            table.add_row(
                str(idx),
                str(len(scores)),
                f"{np.mean(scores):.4f}",
                f"{np.median(scores):.4f}"
            )

        self.console.print(table)

    def print_general_stats(self, title: str, grouped_scores: Dict[str, List[float]], all_scores: np.ndarray):
        stats_table = Table(title=title)
        stats_table.add_column("Métrica", style="white")
        stats_table.add_column("Valor", justify="right", style="yellow")

        stats_table.add_row("Total de queries originais", str(len(grouped_scores)))
        stats_table.add_row("Total de paráfrases", str(len(all_scores)))
        stats_table.add_row("Média geral dos scores", f"{np.mean(all_scores):.4f}")
        stats_table.add_row("Mediana geral dos scores", f"{np.median(all_scores):.4f}")
        stats_table.add_row("Desvio padrão geral", f"{np.std(all_scores):.4f}")

        self.console.print(stats_table)

    def evaluate_and_print(self, pairs: List[Tuple[str, str]]):
        cross_scores = self.evaluate_cross_encoder(pairs)
        cross_grouped = self._group_by_original(pairs, cross_scores)
        self.print_grouped_table("Cross-Encoder: Análise por Query Original", cross_grouped)
        self.print_general_stats("Cross-Encoder: Estatísticas Gerais", cross_grouped, cross_scores)

        sbert_scores = self.evaluate_sbert(pairs)
        sbert_grouped = self._group_by_original(pairs, sbert_scores)
        self.print_grouped_table("Sentence-BERT: Análise por Query Original", sbert_grouped)
        self.print_general_stats("Sentence-BERT: Estatísticas Gerais", sbert_grouped, sbert_scores)

        bleu_scores = self.evaluate_bleu(pairs)
        bleu_grouped = self._group_by_original(pairs, bleu_scores)
        self.print_grouped_table("BLEU Score: Análise por Query Original", bleu_grouped)
        self.print_general_stats("BLEU Score: Estatísticas Gerais", bleu_grouped, bleu_scores)

        self.print_comparison_table(cross_grouped, sbert_grouped, bleu_grouped)

    def print_comparison_table(self, cross_grouped: Dict, sbert_grouped: Dict, bleu_grouped: Dict):
        table = Table(title="Comparação das Três Métricas por Query Original", show_lines=True)
        table.add_column("ID", justify="center", style="white")
        table.add_column("N", justify="center", style="orchid")
        table.add_column("Cross-Enc\nMédia", justify="right", style="yellow")
        table.add_column("Cross-Enc\nMediana", justify="right", style="green")
        table.add_column("SBERT\nMédia", justify="right", style="yellow")
        table.add_column("SBERT\nMediana", justify="right", style="green")
        table.add_column("BLEU\nMédia", justify="right", style="yellow")
        table.add_column("BLEU\nMediana", justify="right", style="green")

        for idx, original in enumerate(cross_grouped.keys(), 1):
            table.add_row(
                str(idx),
                str(len(cross_grouped[original])),
                f"{np.mean(cross_grouped[original]):.4f}",
                f"{np.median(cross_grouped[original]):.4f}",
                f"{np.mean(sbert_grouped[original]):.4f}",
                f"{np.median(sbert_grouped[original]):.4f}",
                f"{np.mean(bleu_grouped[original]):.4f}",
                f"{np.median(bleu_grouped[original]):.4f}"
            )

        self.console.print(table)