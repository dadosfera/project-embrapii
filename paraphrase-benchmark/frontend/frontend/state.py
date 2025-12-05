import reflex as rx
import httpx
from typing import List, Dict, Any, Optional
import os


API_URL = os.getenv("API_URL", "http://localhost:8001")


# === Pipeline Models ===

class QuestionItem(rx.Base):
    """Uma pergunta gerada com metadados."""
    nl_query: str = ""
    complexity: str = "simple"
    query_type: str = "filter"
    tables_involved: List[str] = []
    description: str = ""
    selected: bool = True


class SQLPairItem(rx.Base):
    """Par pergunta + SQL gerado."""
    nl_query: str = ""
    sql_query: str = ""
    complexity: str = "simple"
    query_type: str = "filter"
    tables_involved: List[str] = []
    description: str = ""
    sql_explanation: str = ""


class ParaphraseResultItem(rx.Base):
    """Par com paráfrase."""
    nl_query: str = ""
    sql_query: str = ""
    original_nl_query: str = ""
    is_original: bool = False
    complexity: str = "simple"
    query_type: str = "filter"
    tables_involved: List[str] = []


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
    
    def go_to_pipeline(self):
        """Navega para a página do pipeline."""
        self.current_page = "pipeline"


class PipelineState(rx.State):
    """Estado do pipeline de geração NL-SQL."""
    
    # Sessão atual
    session_id: Optional[int] = None
    
    # Step atual (1-6)
    current_step: int = 1
    
    # Configuração do modelo LLM
    selected_provider: str = "openai"
    selected_model: str = "gpt-4o"
    available_providers: List[Dict[str, Any]] = []
    
    # Step 1: Schema
    schema_input: str = ""
    num_questions: int = 50
    context_input: str = ""
    
    # Step 2: Perguntas geradas
    questions: List[QuestionItem] = []
    
    # Step 3: Pares SQL
    sql_pairs: List[SQLPairItem] = []
    
    # Step 4-5: Paráfrases
    paraphrases: List[ParaphraseResultItem] = []
    num_paraphrases: int = 5
    
    # Step 6: Avaliação (usa métricas do State principal)
    evaluation_results: List[ResultItem] = []
    pipeline_cross_encoder_avg: float = 0.0
    pipeline_sbert_avg: float = 0.0
    pipeline_bleu_avg: float = 0.0
    
    # Loading e erros
    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""
    
    # Estatísticas
    @rx.var
    def total_questions(self) -> int:
        return len(self.questions)
    
    @rx.var
    def selected_questions_count(self) -> int:
        return len([q for q in self.questions if q.selected])
    
    @rx.var
    def total_sql_pairs(self) -> int:
        return len(self.sql_pairs)
    
    @rx.var
    def total_paraphrases(self) -> int:
        return len(self.paraphrases)
    
    @rx.var
    def original_count(self) -> int:
        return len([p for p in self.paraphrases if p.is_original])
    
    @rx.var
    def paraphrase_only_count(self) -> int:
        return len([p for p in self.paraphrases if not p.is_original])
    
    @rx.var
    def step_titles(self) -> List[str]:
        return [
            "Schema",
            "Curadoria",
            "Gerar SQL",
            "Paráfrases",
            "SQL Paráfrases",
            "Avaliação"
        ]
    
    def update_schema(self, value: str):
        """Atualiza o schema input."""
        self.schema_input = value
    
    def update_context(self, value: str):
        """Atualiza o contexto."""
        self.context_input = value
    
    def update_num_questions(self, value: str):
        """Atualiza número de perguntas."""
        try:
            self.num_questions = int(value)
        except ValueError:
            pass
    
    def update_num_paraphrases(self, value: str):
        """Atualiza número de paráfrases."""
        try:
            self.num_paraphrases = int(value)
        except ValueError:
            pass
    
    def toggle_question_selection(self, index: int):
        """Alterna seleção de uma pergunta."""
        if 0 <= index < len(self.questions):
            new_questions = list(self.questions)
            q = new_questions[index]
            new_questions[index] = QuestionItem(
                nl_query=q.nl_query,
                complexity=q.complexity,
                query_type=q.query_type,
                tables_involved=q.tables_involved,
                description=q.description,
                selected=not q.selected
            )
            self.questions = new_questions
    
    def select_all_questions(self):
        """Seleciona todas as perguntas."""
        self.questions = [
            QuestionItem(
                nl_query=q.nl_query,
                complexity=q.complexity,
                query_type=q.query_type,
                tables_involved=q.tables_involved,
                description=q.description,
                selected=True
            )
            for q in self.questions
        ]
    
    def deselect_all_questions(self):
        """Desseleciona todas as perguntas."""
        self.questions = [
            QuestionItem(
                nl_query=q.nl_query,
                complexity=q.complexity,
                query_type=q.query_type,
                tables_involved=q.tables_involved,
                description=q.description,
                selected=False
            )
            for q in self.questions
        ]
    
    def update_question_text(self, index: int, value: str):
        """Atualiza texto de uma pergunta."""
        if 0 <= index < len(self.questions):
            new_questions = list(self.questions)
            q = new_questions[index]
            new_questions[index] = QuestionItem(
                nl_query=value,
                complexity=q.complexity,
                query_type=q.query_type,
                tables_involved=q.tables_involved,
                description=q.description,
                selected=q.selected
            )
            self.questions = new_questions
    
    def update_sql_query(self, index: int, value: str):
        """Atualiza SQL de um par."""
        if 0 <= index < len(self.sql_pairs):
            new_pairs = list(self.sql_pairs)
            p = new_pairs[index]
            new_pairs[index] = SQLPairItem(
                nl_query=p.nl_query,
                sql_query=value,
                complexity=p.complexity,
                query_type=p.query_type,
                tables_involved=p.tables_involved,
                description=p.description,
                sql_explanation=p.sql_explanation
            )
            self.sql_pairs = new_pairs
    
    def go_to_step(self, step: int):
        """Navega para um step específico."""
        if 1 <= step <= 6:
            self.current_step = step
            self.error_message = ""
            self.success_message = ""
    
    def next_step(self):
        """Avança para o próximo step."""
        if self.current_step < 6:
            self.current_step += 1
            self.error_message = ""
            self.success_message = ""
    
    def prev_step(self):
        """Volta para o step anterior."""
        if self.current_step > 1:
            self.current_step -= 1
            self.error_message = ""
            self.success_message = ""
    
    def reset_pipeline(self):
        """Reseta todo o pipeline."""
        self.session_id = None
        self.current_step = 1
        self.schema_input = ""
        self.num_questions = 50
        self.context_input = ""
        self.questions = []
        self.sql_pairs = []
        self.paraphrases = []
        self.num_paraphrases = 5
        self.evaluation_results = []
        self.pipeline_cross_encoder_avg = 0.0
        self.pipeline_sbert_avg = 0.0
        self.pipeline_bleu_avg = 0.0
        self.error_message = ""
        self.success_message = ""
    
    async def load_providers(self):
        """Carrega lista de provedores disponíveis."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{API_URL}/api/pipeline/providers")
                if response.status_code == 200:
                    data = response.json()
                    self.available_providers = data.get("providers", [])
                    current = data.get("current")
                    if current:
                        self.selected_provider = current.get("provider", "openai")
                        self.selected_model = current.get("model", "gpt-4o")
        except Exception:
            pass  # Silently fail, will use defaults
    
    async def set_provider(self, provider: str, model: str):
        """Define o provedor e modelo."""
        self.error_message = ""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{API_URL}/api/pipeline/set-provider",
                    params={"provider": provider, "model": model}
                )
                if response.status_code == 200:
                    data = response.json()
                    info = data.get("model_info", {})
                    self.selected_provider = info.get("provider", provider)
                    self.selected_model = info.get("model", model)
                    self.success_message = f"Modelo alterado: {self.selected_model}"
                else:
                    self.error_message = f"Erro ao trocar modelo: {response.text}"
        except Exception as e:
            self.error_message = f"Erro: {str(e)}"
    
    def update_provider(self, provider: str):
        """Atualiza provedor selecionado."""
        self.selected_provider = provider
        # Define modelo padrão para o provedor
        default_models = {
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022",
            "google": "gemini-2.0-flash"
        }
        self.selected_model = default_models.get(provider, "gpt-4o")
    
    def update_model(self, model: str):
        """Atualiza modelo selecionado."""
        self.selected_model = model
    
    async def generate_questions(self):
        """Step 1: Gera perguntas a partir do schema."""
        if not self.schema_input.strip():
            self.error_message = "Por favor, cole o schema do banco de dados."
            return
        
        self.is_loading = True
        self.error_message = ""
        self.success_message = ""
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                # Configura o provedor antes de gerar
                await client.post(
                    f"{API_URL}/api/pipeline/set-provider",
                    params={"provider": self.selected_provider, "model": self.selected_model}
                )
                
                response = await client.post(
                    f"{API_URL}/api/pipeline/generate-questions",
                    json={
                        "schema": self.schema_input,
                        "num_questions": self.num_questions,
                        "context": self.context_input if self.context_input.strip() else None
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.session_id = data["session_id"]
                    self.questions = [
                        QuestionItem(
                            nl_query=q["nl_query"],
                            complexity=q["complexity"],
                            query_type=q["query_type"],
                            tables_involved=q.get("tables_involved", []),
                            description=q.get("description", ""),
                            selected=q.get("selected", True)
                        )
                        for q in data["questions"]
                    ]
                    self.success_message = f"✅ {data['total_generated']} perguntas geradas!"
                    self.current_step = 2
                else:
                    self.error_message = f"Erro ao gerar perguntas: {response.text}"
                    
        except httpx.TimeoutException:
            self.error_message = "Timeout: A geração demorou muito. Tente novamente."
        except Exception as e:
            self.error_message = f"Erro de conexão: {str(e)}"
        finally:
            self.is_loading = False
    
    async def generate_sql(self):
        """Step 3: Gera SQLs para as perguntas selecionadas."""
        selected = [q for q in self.questions if q.selected]
        
        if not selected:
            self.error_message = "Selecione pelo menos uma pergunta."
            return
        
        self.is_loading = True
        self.error_message = ""
        self.success_message = ""
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{API_URL}/api/pipeline/generate-sql",
                    json={
                        "session_id": self.session_id,
                        "schema": self.schema_input,
                        "questions": [
                            {
                                "nl_query": q.nl_query,
                                "complexity": q.complexity,
                                "query_type": q.query_type,
                                "tables_involved": q.tables_involved,
                                "description": q.description,
                                "selected": q.selected
                            }
                            for q in selected
                        ]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.sql_pairs = [
                        SQLPairItem(
                            nl_query=p["nl_query"],
                            sql_query=p["sql_query"],
                            complexity=p["complexity"],
                            query_type=p["query_type"],
                            tables_involved=p.get("tables_involved", []),
                            description=p.get("description", ""),
                            sql_explanation=p.get("sql_explanation", "")
                        )
                        for p in data["pairs"]
                    ]
                    self.success_message = f"✅ {data['total_pairs']} consultas SQL geradas!"
                    self.current_step = 4
                else:
                    self.error_message = f"Erro ao gerar SQLs: {response.text}"
                    
        except httpx.TimeoutException:
            self.error_message = "Timeout: A geração demorou muito."
        except Exception as e:
            self.error_message = f"Erro de conexão: {str(e)}"
        finally:
            self.is_loading = False
    
    async def generate_paraphrases(self):
        """Step 4: Gera paráfrases das perguntas."""
        if not self.sql_pairs:
            self.error_message = "Não há pares para gerar paráfrases."
            return
        
        self.is_loading = True
        self.error_message = ""
        self.success_message = ""
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{API_URL}/api/pipeline/generate-paraphrases",
                    json={
                        "session_id": self.session_id,
                        "pairs": [
                            {
                                "nl_query": p.nl_query,
                                "sql_query": p.sql_query,
                                "complexity": p.complexity,
                                "query_type": p.query_type,
                                "tables_involved": p.tables_involved,
                                "description": p.description
                            }
                            for p in self.sql_pairs
                        ],
                        "num_paraphrases": self.num_paraphrases
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.paraphrases = [
                        ParaphraseResultItem(
                            nl_query=p["nl_query"],
                            sql_query=p.get("sql_query", ""),
                            original_nl_query=p["original_nl_query"],
                            is_original=p["is_original"],
                            complexity=p["complexity"],
                            query_type=p["query_type"],
                            tables_involved=p.get("tables_involved", [])
                        )
                        for p in data["paraphrases"]
                    ]
                    self.success_message = f"✅ {data['total_paraphrases']} paráfrases geradas!"
                    self.current_step = 5
                else:
                    self.error_message = f"Erro ao gerar paráfrases: {response.text}"
                    
        except httpx.TimeoutException:
            self.error_message = "Timeout: A geração demorou muito."
        except Exception as e:
            self.error_message = f"Erro de conexão: {str(e)}"
        finally:
            self.is_loading = False
    
    async def regenerate_sql(self):
        """Step 5: Regenera SQLs para as paráfrases."""
        if not self.paraphrases:
            self.error_message = "Não há paráfrases para regenerar SQL."
            return
        
        self.is_loading = True
        self.error_message = ""
        self.success_message = ""
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{API_URL}/api/pipeline/regenerate-sql",
                    json={
                        "session_id": self.session_id,
                        "schema": self.schema_input,
                        "paraphrases": [
                            {
                                "nl_query": p.nl_query,
                                "sql_query": p.sql_query,
                                "original_nl_query": p.original_nl_query,
                                "is_original": p.is_original,
                                "complexity": p.complexity,
                                "query_type": p.query_type,
                                "tables_involved": p.tables_involved
                            }
                            for p in self.paraphrases
                        ]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.paraphrases = [
                        ParaphraseResultItem(
                            nl_query=p["nl_query"],
                            sql_query=p.get("sql_query", ""),
                            original_nl_query=p["original_nl_query"],
                            is_original=p["is_original"],
                            complexity=p["complexity"],
                            query_type=p["query_type"],
                            tables_involved=p.get("tables_involved", [])
                        )
                        for p in data["pairs"]
                    ]
                    self.success_message = f"✅ {data['total_pairs']} SQLs regenerados!"
                    self.current_step = 6
                else:
                    self.error_message = f"Erro ao regenerar SQLs: {response.text}"
                    
        except httpx.TimeoutException:
            self.error_message = "Timeout: A geração demorou muito."
        except Exception as e:
            self.error_message = f"Erro de conexão: {str(e)}"
        finally:
            self.is_loading = False
    
    async def run_evaluation(self):
        """Step 6: Executa avaliação das paráfrases."""
        if not self.paraphrases:
            self.error_message = "Não há paráfrases para avaliar."
            return
        
        # Prepara pares para avaliação (original vs paráfrase)
        pairs_to_evaluate = []
        for p in self.paraphrases:
            if not p.is_original and p.original_nl_query:
                pairs_to_evaluate.append({
                    "original": p.original_nl_query,
                    "paraphrase": p.nl_query
                })
        
        if not pairs_to_evaluate:
            self.error_message = "Não há pares de paráfrases para avaliar."
            return
        
        self.is_loading = True
        self.error_message = ""
        self.success_message = ""
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{API_URL}/api/evaluate",
                    json={"pairs": pairs_to_evaluate}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.evaluation_results = [
                        ResultItem(
                            original=r["original"],
                            paraphrase=r["paraphrase"],
                            cross_encoder=r["cross_encoder"],
                            sbert=r["sbert"],
                            bleu=r["bleu"]
                        )
                        for r in data["results"]
                    ]
                    self.pipeline_cross_encoder_avg = data["summary"]["cross_encoder_avg"]
                    self.pipeline_sbert_avg = data["summary"]["sbert_avg"]
                    self.pipeline_bleu_avg = data["summary"]["bleu_avg"]
                    self.success_message = f"✅ Avaliação concluída! {len(pairs_to_evaluate)} pares avaliados."
                else:
                    self.error_message = f"Erro na avaliação: {response.text}"
                    
        except httpx.TimeoutException:
            self.error_message = "Timeout: A avaliação demorou muito."
        except Exception as e:
            self.error_message = f"Erro de conexão: {str(e)}"
        finally:
            self.is_loading = False
