from src.base import TextToSQLBase
from src.vendor.m_schema import SchemaEngine

from huggingface_hub import snapshot_download, InferenceClient
from sqlalchemy import create_engine
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline,
)
import json
import os
import torch


# ----------------------------------------------------------------------------
# Templates de prompt
# ----------------------------------------------------------------------------
# Template OFICIAL (chinês), conforme o card do modelo XiYanSQL-QwenCoder. É o
# template com que o modelo foi treinado; o próprio card recomenda usá-lo (e o
# formato M-Schema) para melhor desempenho. Os placeholders {dialect},
# {question}, {db_schema} e {evidence} são preenchidos em runtime.
NL2SQL_TEMPLATE_CN = """你是一名{dialect}专家，现在需要阅读并理解下面的【数据库schema】描述，以及可能用到的【参考信息】，并运用{dialect}知识生成sql语句回答【用户问题】。
【用户问题】
{question}

【数据库schema】
{db_schema}

【参考信息】
{evidence}

【用户问题】
{question}

```sql"""

# Alternativa em INGLÊS (do README do M-Schema). Selecionável via PROMPT_LANG.
# Mantida porque as perguntas do nosso benchmark são em português e pode ser
# preferível instruções em inglês a chinês em alguns experimentos.
NL2SQL_TEMPLATE_EN = """You are now a {dialect} data analyst, and you are given a database schema as follows:

【Schema】
{db_schema}

【Question】
{question}

【Evidence】
{evidence}

Please read and understand the database schema carefully, and generate an executable SQL based on the user's question and evidence. The generated SQL is protected by ```sql and ```.
"""

# "cn" = template oficial (recomendado pelo card) | "en" = alternativa em inglês.
PROMPT_LANG = "cn"

# SGBD (SQLAlchemy dialect.name) -> rótulo de dialeto esperado pelo modelo.
DIALECT_MAP = {"sqlite": "SQLite", "postgresql": "PostgreSQL", "mysql": "MySQL"}


class XiYanSQL(TextToSQLBase):

    def __init__(self, db_config, model_id, hf_token, local_model=True,
                 doc_path=None, examples_path=None):
        self.model_id = model_id
        self.hf_token = hf_token
        self.local_model = local_model
        self.doc_path = doc_path
        self.examples_path = examples_path

        self._mschema_cache = {}

        self.evidence = self._build_evidence()

        if db_config is not None:
            self._connect_database(db_config)

        self._set_model()

    def generate_query(self, question: str, t: int = 1024, db_config: dict = None) -> str:
        if db_config is not None:
            self._connect_database(db_config)

        mschema_str = self._get_mschema()
        messages = self._build_prompt(mschema_str, question)

        if self.local_model:
            raw = self._infer_local(messages, max_new_tokens=t)
        else:
            raw = self._infer_api(messages, max_new_tokens=t)

        return self._extract_sql(raw)

    def _connect_database(self, db_config):
        self.SGBD = db_config["SGBD"]

        if self.SGBD == "sqlite":
            db_path = db_config["db_path"]
            self.db_uri = f"sqlite:///{os.path.abspath(db_path)}"
            self.db_name = os.path.splitext(os.path.basename(db_path))[0]
        elif self.SGBD == "postgresql":
            user = db_config.get("user", "postgres")
            password = db_config.get("password", "")
            host = db_config.get("host", "localhost")
            port = db_config.get("port", "5432")
            db_name = db_config.get("db_name", "")
            self.db_uri = (
                f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
                "?sslmode=disable"
            )
            self.db_name = db_name
        else:
            raise ValueError(f"SGBD não suportado: {self.SGBD}")

        self.engine = create_engine(self.db_uri)

    def _get_mschema(self) -> str:
        """Constrói (e cacheia) a representação M-Schema do banco atual."""
        if self.db_uri not in self._mschema_cache:
            schema_engine = SchemaEngine(engine=self.engine, db_name=self.db_name)
            self._mschema_cache[self.db_uri] = schema_engine.mschema.to_mschema()
        return self._mschema_cache[self.db_uri]


    def _build_prompt(self, db_schema: str, question: str):
        dialect = DIALECT_MAP.get(self.SGBD, self.SGBD)

        lang = os.getenv("XIYAN_PROMPT_LANG", PROMPT_LANG)
        template = NL2SQL_TEMPLATE_CN if lang == "cn" else NL2SQL_TEMPLATE_EN
        prompt = template.format(
            dialect=dialect,
            db_schema=db_schema,
            question=question,
            evidence=self.evidence,
        )
        return [{"role": "user", "content": prompt}]

    def _build_evidence(self) -> str:
        """
        Monta o campo {evidence} com documentação (.md) e/ou exemplos (.json),
        nos mesmos moldes das variantes do VannaAi.
        """
        parts = []

        if self.doc_path:
            if os.path.exists(self.doc_path):
                with open(self.doc_path, "r", encoding="utf-8") as f:
                    parts.append(f.read().strip())
            else:
                print(f"Aviso: documentação {self.doc_path} não encontrada.")

        if self.examples_path:
            if os.path.exists(self.examples_path):
                with open(self.examples_path, "r", encoding="utf-8") as f:
                    exemplos = json.load(f)
                linhas = []
                for item in exemplos:
                    pergunta = item.get("question")
                    sql = item.get("sql")
                    if pergunta and sql:
                        linhas.append(f"Pergunta: {pergunta}\nSQL: {sql}")
                if linhas:
                    parts.append(
                        "Exemplos de pares (pergunta, SQL):\n" + "\n\n".join(linhas)
                    )
            else:
                print(f"Aviso: exemplos {self.examples_path} não encontrados.")

        return "\n\n".join(parts)


    def _set_model(self):
        if self.local_model:
            folder_name = self.model_id.replace("/", "-")
            self.model_path = os.path.join("./local_models/", folder_name)
            self._ensure_model_downloaded()
            self._load_local_pipeline()
        else:
            self.client = InferenceClient(model=self.model_id, token=self.hf_token)
            self.pipe = None

    def _ensure_model_downloaded(self):
        if not os.path.exists(self.model_path):
            print(f"Baixando modelo para {self.model_path}...")
            snapshot_download(
                repo_id=self.model_id,
                local_dir=self.model_path,
                token=self.hf_token,
            )
            print("Download concluído.")
        else:
            print("Modelo já presente localmente.")

    def _load_local_pipeline(self):
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

        tokenizer = AutoTokenizer.from_pretrained(self.model_path, token=self.hf_token)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token_id = tokenizer.eos_token_id

        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            token=self.hf_token,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )

        self.pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)


    def _infer_local(self, messages, max_new_tokens=1024):
        outputs = self.pipe(
            messages,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.1,
            top_p=0.8,
            return_full_text=False,
        )
        return outputs[0]["generated_text"]

    def _infer_api(self, messages, max_new_tokens=1024):
        response = self.client.chat_completion(
            messages=messages,
            max_tokens=max_new_tokens,
            temperature=0.1,
            top_p=0.8,
        )
        return response.choices[0].message.content

    def _extract_sql(self, raw_output: str) -> str:
        """
        O prompt termina em "```sql"; a saída do modelo é a continuação
        (o SQL), normalmente encerrada por "```". Removemos fences residuais.
        """
        text = raw_output.strip()

        if text.startswith("```sql"):
            text = text[len("```sql"):]
        elif text.startswith("```"):
            text = text[3:]

        if "```" in text:
            text = text.split("```")[0]

        return text.strip()
