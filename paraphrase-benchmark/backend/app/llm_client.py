"""Cliente multi-provedor para geração de perguntas, SQLs e paráfrases."""

import os
import json
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


# === Base Class ===

class BaseLLMClient(ABC):
    """Classe base para clientes LLM."""
    
    provider: str = "base"
    model: str = ""
    
    @abstractmethod
    def chat(self, messages: List[Dict], temperature: float = 0.7, json_mode: bool = False) -> str:
        """Envia mensagens e retorna resposta."""
        pass
    
    def get_info(self) -> Dict[str, str]:
        """Retorna informações do modelo."""
        return {"provider": self.provider, "model": self.model}


# === OpenAI Client ===

class OpenAIClient(BaseLLMClient):
    """Cliente para OpenAI (GPT-4, GPT-3.5, etc)."""
    
    provider = "openai"
    
    def __init__(self, model: str = "gpt-4o"):
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada")
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def chat(self, messages: List[Dict], temperature: float = 0.7, json_mode: bool = False) -> str:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


# === Anthropic Client ===

class AnthropicClient(BaseLLMClient):
    """Cliente para Anthropic (Claude)."""
    
    provider = "anthropic"
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY não configurada")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def chat(self, messages: List[Dict], temperature: float = 0.7, json_mode: bool = False) -> str:
        # Separa system message das outras
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)
        
        # Adiciona instrução de JSON se necessário
        if json_mode and chat_messages:
            chat_messages[-1]["content"] += "\n\nIMPORTANTE: Retorne APENAS JSON válido, sem markdown ou texto adicional."
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_msg,
            messages=chat_messages,
            temperature=temperature
        )
        return response.content[0].text


# === Google Client ===

class GoogleClient(BaseLLMClient):
    """Cliente para Google (Gemini)."""
    
    provider = "google"
    
    def __init__(self, model: str = "gemini-1.5-pro"):
        import google.generativeai as genai
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não configurada")
        genai.configure(api_key=api_key)
        self.model = model
        self.genai = genai
    
    def chat(self, messages: List[Dict], temperature: float = 0.7, json_mode: bool = False) -> str:
        # Converte mensagens para formato Gemini
        model = self.genai.GenerativeModel(self.model)
        
        # Combina system + user messages
        full_prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                full_prompt += f"Instruções do sistema: {msg['content']}\n\n"
            else:
                full_prompt += f"{msg['content']}\n"
        
        if json_mode:
            full_prompt += "\n\nIMPORTANTE: Retorne APENAS JSON válido, sem markdown ou texto adicional."
        
        generation_config = self.genai.GenerationConfig(temperature=temperature)
        response = model.generate_content(full_prompt, generation_config=generation_config)
        return response.text


# === Factory ===

PROVIDERS = {
    "openai": {
        "client": OpenAIClient,
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "env_key": "OPENAI_API_KEY"
    },
    "anthropic": {
        "client": AnthropicClient,
        "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        "env_key": "ANTHROPIC_API_KEY"
    },
    "google": {
        "client": GoogleClient,
        "models": ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-pro"],
        "env_key": "GOOGLE_API_KEY"
    }
}


def get_available_providers() -> List[Dict[str, Any]]:
    """Retorna lista de provedores disponíveis (com API key configurada)."""
    available = []
    for provider_name, config in PROVIDERS.items():
        env_key = config["env_key"]
        is_configured = bool(os.getenv(env_key))
        available.append({
            "provider": provider_name,
            "models": config["models"],
            "configured": is_configured,
            "env_key": env_key
        })
    return available


def create_llm_client(provider: str = "openai", model: Optional[str] = None) -> BaseLLMClient:
    """Cria cliente LLM para o provedor especificado."""
    if provider not in PROVIDERS:
        raise ValueError(f"Provedor '{provider}' não suportado. Use: {list(PROVIDERS.keys())}")
    
    config = PROVIDERS[provider]
    client_class = config["client"]
    
    if model is None:
        model = config["models"][0]  # Modelo padrão
    
    return client_class(model=model)


# === LLM Generator ===

class LLMGenerator:
    """Classe para geração de perguntas, SQLs e paráfrases."""
    
    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        self.client = create_llm_client(provider, model)
        self.provider = provider
        self.model = self.client.model
    
    def get_model_info(self) -> Dict[str, str]:
        """Retorna informações do modelo atual."""
        return {"provider": self.provider, "model": self.model}
    
    async def generate_questions(
        self, 
        schema: str, 
        num_questions: int = 50,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Gera perguntas em linguagem natural baseadas no schema do banco."""
        
        system_prompt = """Você é um especialista em bancos de dados e geração de consultas SQL.
Sua tarefa é gerar perguntas em linguagem natural que possam ser respondidas usando o schema fornecido.

As perguntas devem:
- Ser diversas em complexidade (simples, média, complexa)
- Cobrir diferentes tipos de consultas (filtros, agregações, joins, subqueries)
- Ser realistas e úteis para análises de negócio
- Estar em português brasileiro

Para cada pergunta, retorne um JSON com:
- nl_query: A pergunta em linguagem natural
- complexity: "simple", "medium" ou "complex"
- query_type: Tipo principal da consulta (filter, aggregation, join, subquery, window)
- tables_involved: Lista de tabelas envolvidas
- description: Breve descrição do objetivo da consulta"""

        user_prompt = f"""Schema do banco de dados:
```sql
{schema}
```

{f"Contexto adicional: {context}" if context else ""}

Gere exatamente {num_questions} perguntas diversas em linguagem natural que possam ser respondidas com consultas SQL neste schema.

Retorne APENAS um JSON válido no formato:
{{
  "questions": [
    {{
      "nl_query": "...",
      "complexity": "simple|medium|complex",
      "query_type": "filter|aggregation|join|subquery|window",
      "tables_involved": ["tabela1", "tabela2"],
      "description": "..."
    }}
  ]
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat(messages, temperature=0.8, json_mode=True)
        
        # Tenta extrair JSON da resposta
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Tenta extrair JSON de markdown
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(response.strip())
        
        return result.get("questions", [])
    
    async def generate_sql(
        self, 
        schema: str, 
        questions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Gera consultas SQL para as perguntas fornecidas."""
        
        system_prompt = """Você é um especialista em SQL.
Sua tarefa é gerar consultas SQL corretas e otimizadas para responder às perguntas em linguagem natural.

As consultas devem:
- Ser sintaticamente corretas para PostgreSQL
- Usar aliases apropriados
- Ser bem formatadas e legíveis
- Retornar dados relevantes para a pergunta"""

        questions_text = "\n".join([
            f"{i+1}. {q['nl_query']}" 
            for i, q in enumerate(questions)
        ])
        
        user_prompt = f"""Schema do banco de dados:
```sql
{schema}
```

Perguntas para gerar SQL:
{questions_text}

Gere a consulta SQL correspondente para CADA pergunta.

Retorne APENAS um JSON válido no formato:
{{
  "sql_queries": [
    {{
      "question_index": 0,
      "nl_query": "...",
      "sql_query": "SELECT ...",
      "explanation": "Breve explicação da lógica"
    }}
  ]
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat(messages, temperature=0.3, json_mode=True)
        
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(response.strip())
        
        sql_queries = result.get("sql_queries", [])
        
        enriched_results = []
        for i, question in enumerate(questions):
            sql_item = next(
                (sq for sq in sql_queries if sq.get("question_index") == i),
                None
            )
            enriched_results.append({
                **question,
                "sql_query": sql_item["sql_query"] if sql_item else "",
                "sql_explanation": sql_item.get("explanation", "") if sql_item else ""
            })
        
        return enriched_results
    
    async def generate_paraphrases(
        self, 
        pairs: List[Dict[str, Any]], 
        num_paraphrases: int = 5
    ) -> List[Dict[str, Any]]:
        """Gera paráfrases para as perguntas originais."""
        
        system_prompt = f"""Você é um especialista em paráfrases de texto.
Sua tarefa é gerar {num_paraphrases} variações de perguntas em linguagem natural,
mantendo o mesmo significado semântico.

As paráfrases devem:
- Preservar a intenção original da pergunta
- Variar a estrutura da frase significativamente
- Podem alterar valores específicos (anos, números) para aumentar diversidade
- Manter naturalidade em português brasileiro
- NÃO alterar o significado fundamental da consulta"""

        questions_text = "\n".join([
            f"{i+1}. {p['nl_query']}" 
            for i, p in enumerate(pairs)
        ])
        
        user_prompt = f"""Perguntas originais:
{questions_text}

Gere {num_paraphrases} paráfrases diversas para CADA pergunta acima.

Retorne APENAS um JSON válido no formato:
{{
  "paraphrases": [
    {{
      "original_index": 0,
      "original_query": "pergunta original",
      "variations": [
        "paráfrase 1",
        "paráfrase 2"
      ]
    }}
  ]
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat(messages, temperature=0.9, json_mode=True)
        
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(response.strip())
        
        paraphrases_data = result.get("paraphrases", [])
        
        expanded_pairs = []
        for i, pair in enumerate(pairs):
            expanded_pairs.append({
                **pair,
                "is_original": True,
                "original_nl_query": pair["nl_query"]
            })
            
            paraphrase_item = next(
                (p for p in paraphrases_data if p.get("original_index") == i),
                None
            )
            
            if paraphrase_item:
                for variation in paraphrase_item.get("variations", []):
                    expanded_pairs.append({
                        **pair,
                        "nl_query": variation,
                        "is_original": False,
                        "original_nl_query": pair["nl_query"],
                        "sql_query": ""
                    })
        
        return expanded_pairs
    
    async def regenerate_sql_for_paraphrases(
        self, 
        schema: str, 
        paraphrase_pairs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Regenera SQLs para as paráfrases, garantindo consistência."""
        
        paraphrases_needing_sql = [
            p for p in paraphrase_pairs 
            if not p.get("is_original", False)
        ]
        
        if not paraphrases_needing_sql:
            return paraphrase_pairs
        
        system_prompt = """Você é um especialista em SQL.
Sua tarefa é gerar consultas SQL que correspondam semanticamente às perguntas parafraseadas.

IMPORTANTE: 
- A paráfrase pode ter pequenas variações na intenção
- A SQL deve refletir exatamente o que a paráfrase pede
- Seja consistente com o schema fornecido"""

        questions_with_context = []
        for i, p in enumerate(paraphrases_needing_sql):
            questions_with_context.append(
                f"{i+1}. Paráfrase: {p['nl_query']}\n"
                f"   Original: {p['original_nl_query']}\n"
                f"   SQL Original: {p.get('sql_query', 'N/A')}"
            )
        
        user_prompt = f"""Schema do banco de dados:
```sql
{schema}
```

Gere SQLs para as seguintes paráfrases:
{chr(10).join(questions_with_context)}

Retorne APENAS um JSON válido no formato:
{{
  "sql_queries": [
    {{
      "index": 0,
      "sql_query": "SELECT ..."
    }}
  ]
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat(messages, temperature=0.3, json_mode=True)
        
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(response.strip())
        
        new_sqls = result.get("sql_queries", [])
        
        updated_pairs = []
        paraphrase_idx = 0
        
        for pair in paraphrase_pairs:
            if pair.get("is_original", False):
                updated_pairs.append(pair)
            else:
                sql_item = next(
                    (sq for sq in new_sqls if sq.get("index") == paraphrase_idx),
                    None
                )
                updated_pair = {
                    **pair,
                    "sql_query": sql_item["sql_query"] if sql_item else pair.get("sql_query", "")
                }
                updated_pairs.append(updated_pair)
                paraphrase_idx += 1
        
        return updated_pairs


# === Global instance ===

llm_generator: Optional[LLMGenerator] = None
current_provider: str = "openai"
current_model: Optional[str] = None


def get_llm_generator() -> LLMGenerator:
    """Retorna a instância do gerador LLM."""
    global llm_generator
    if llm_generator is None:
        llm_generator = LLMGenerator(provider=current_provider, model=current_model)
    return llm_generator


def init_llm_generator(provider: str = "openai", model: Optional[str] = None) -> LLMGenerator:
    """Inicializa o gerador LLM."""
    global llm_generator, current_provider, current_model
    current_provider = provider
    current_model = model
    llm_generator = LLMGenerator(provider=provider, model=model)
    return llm_generator


def set_llm_provider(provider: str, model: Optional[str] = None) -> Dict[str, str]:
    """Altera o provedor/modelo do LLM em runtime."""
    global llm_generator, current_provider, current_model
    current_provider = provider
    current_model = model
    llm_generator = LLMGenerator(provider=provider, model=model)
    return llm_generator.get_model_info()
