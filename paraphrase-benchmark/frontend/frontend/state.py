import reflex as rx
import httpx
from typing import List, Dict, Any, Optional
import os


API_URL = os.getenv("API_URL", "http://localhost:8001")


class PairItem(rx.Base):
    """Um par de texto original e paráfrase."""
    original: str = ""
    paraphrase: str = ""


class ResultItem(rx.Base):
    """Resultado de avaliação de um par."""
    original: str
    paraphrase: str
    cross_encoder: float
    sbert: float
    bleu: float


class HistoryItem(rx.Base):
    """Item do histórico de avaliações."""
    id: int
    created_at: str
    total_pairs: int
    cross_encoder_avg: float
    sbert_avg: float
    bleu_avg: float


class State(rx.State):
    """Estado global da aplicação."""
    
    # Estado do formulário
    pairs: List[PairItem] = [PairItem()]
    
    # Estado dos resultados
    results: List[ResultItem] = []
    cross_encoder_avg: float = 0.0
    sbert_avg: float = 0.0
    bleu_avg: float = 0.0
    total_pairs: int = 0
    last_evaluation_id: Optional[int] = None
    
    # Estado do histórico
    history: List[HistoryItem] = []
    
    # Estado de loading
    is_loading: bool = False
    error_message: str = ""
    
    # Página atual
    current_page: str = "evaluate"
    
    @rx.var
    def cross_encoder_display(self) -> str:
        """Retorna cross_encoder formatado."""
        return f"{self.cross_encoder_avg:.3f}"
    
    @rx.var
    def sbert_display(self) -> str:
        """Retorna sbert formatado."""
        return f"{self.sbert_avg:.3f}"
    
    @rx.var
    def bleu_display(self) -> str:
        """Retorna bleu formatado."""
        return f"{self.bleu_avg:.1f}"
    
    def add_pair(self):
        """Adiciona um novo par vazio ao formulário."""
        self.pairs = self.pairs + [PairItem()]
    
    def remove_pair(self, index: int):
        """Remove um par do formulário."""
        if len(self.pairs) > 1:
            self.pairs = [p for i, p in enumerate(self.pairs) if i != index]
    
    def update_original(self, index: int, value: str):
        """Atualiza o texto original de um par."""
        new_pairs = list(self.pairs)
        new_pairs[index] = PairItem(original=value, paraphrase=self.pairs[index].paraphrase)
        self.pairs = new_pairs
    
    def update_paraphrase(self, index: int, value: str):
        """Atualiza a paráfrase de um par."""
        new_pairs = list(self.pairs)
        new_pairs[index] = PairItem(original=self.pairs[index].original, paraphrase=value)
        self.pairs = new_pairs
    
    def clear_form(self):
        """Limpa o formulário."""
        self.pairs = [PairItem()]
        self.results = []
        self.cross_encoder_avg = 0.0
        self.sbert_avg = 0.0
        self.bleu_avg = 0.0
        self.total_pairs = 0
        self.error_message = ""
    
    async def evaluate(self):
        """Envia os pares para avaliação."""
        self.is_loading = True
        self.error_message = ""
        self.results = []
        self.cross_encoder_avg = 0.0
        self.sbert_avg = 0.0
        self.bleu_avg = 0.0
        
        try:
            # Filtra pares vazios
            valid_pairs = [
                {"original": p.original, "paraphrase": p.paraphrase}
                for p in self.pairs
                if p.original.strip() and p.paraphrase.strip()
            ]
            
            if not valid_pairs:
                self.error_message = "Adicione pelo menos um par com texto original e paráfrase."
                self.is_loading = False
                return
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{API_URL}/api/evaluate",
                    json={"pairs": valid_pairs}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.results = [
                        ResultItem(
                            original=r["original"],
                            paraphrase=r["paraphrase"],
                            cross_encoder=r["cross_encoder"],
                            sbert=r["sbert"],
                            bleu=r["bleu"]
                        )
                        for r in data["results"]
                    ]
                    self.cross_encoder_avg = data["summary"]["cross_encoder_avg"]
                    self.sbert_avg = data["summary"]["sbert_avg"]
                    self.bleu_avg = data["summary"]["bleu_avg"]
                    self.total_pairs = data["summary"]["total_pairs"]
                    self.last_evaluation_id = data["id"]
                else:
                    self.error_message = f"Erro na avaliação: {response.text}"
                    
        except httpx.TimeoutException:
            self.error_message = "Timeout: A avaliação demorou muito. Tente com menos pares."
        except Exception as e:
            self.error_message = f"Erro de conexão: {str(e)}"
        finally:
            self.is_loading = False
    
    async def load_history(self):
        """Carrega o histórico de avaliações."""
        self.is_loading = True
        self.error_message = ""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_URL}/api/history")
                
                if response.status_code == 200:
                    data = response.json()
                    self.history = [
                        HistoryItem(
                            id=item["id"],
                            created_at=item["created_at"],
                            total_pairs=item["total_pairs"],
                            cross_encoder_avg=item["cross_encoder_avg"],
                            sbert_avg=item["sbert_avg"],
                            bleu_avg=item["bleu_avg"]
                        )
                        for item in data
                    ]
                else:
                    self.error_message = f"Erro ao carregar histórico: {response.text}"
                    
        except Exception as e:
            self.error_message = f"Erro de conexão: {str(e)}"
        finally:
            self.is_loading = False
    
    async def load_evaluation_details(self, evaluation_id: int):
        """Carrega detalhes de uma avaliação específica."""
        pass  # Simplificado para evitar problemas de tipagem
    
    async def delete_evaluation(self, evaluation_id: int):
        """Remove uma avaliação do histórico."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(f"{API_URL}/api/history/{evaluation_id}")
                
                if response.status_code == 200:
                    await self.load_history()
                else:
                    self.error_message = f"Erro ao remover avaliação: {response.text}"
                    
        except Exception as e:
            self.error_message = f"Erro de conexão: {str(e)}"
    
    def go_to_evaluate(self):
        """Navega para a página de avaliação."""
        self.current_page = "evaluate"
    
    def go_to_history(self):
        """Navega para a página de histórico."""
        self.current_page = "history"
