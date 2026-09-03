from src.base import TextToSQLBase

from huggingface_hub import snapshot_download, InferenceClient
from sqlalchemy import create_engine, inspect
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline,
)
import torch
import re
import os


class RawModel(TextToSQLBase):
    """
    Método Text2SQL que usa apenas a inferência direta de um LLM via HuggingFace,
    sem frameworks adicionais. O modelo recebe o esquema do banco e a pergunta
    do usuário e retorna a query SQL gerada.
    """

    def __init__(self, db_config, model_id, hf_token, local_model=True):
        self.model_id = model_id
        self.hf_token = hf_token
        self.local_model = local_model

        self._schema_cache = {}

        if db_config is not None:
            self._connect_database(db_config)

        self._set_model()

    def generate_query(self, question: str, max_new_tokens: int = 512, db_config: dict = None) -> str:
        """
        Recebe uma pergunta em linguagem natural e retorna uma query SQL.

        Args:
            question (str): Pergunta do usuário.
            max_new_tokens (int): Número máximo de tokens gerados pelo modelo.
            db_config (dict): Config de banco opcional (usado pelo Spider, que
                troca de banco a cada pergunta).

        Returns:
            str: Query SQL gerada pelo modelo.
        """
        if db_config is not None:
            self._connect_database(db_config)

        schema = self._get_schema()
        prompt = self._build_prompt(schema, question)

        if self.local_model:
            sql = self._infer_local(prompt, max_new_tokens=max_new_tokens)
        else:
            sql = self._infer_api(prompt, max_new_tokens=max_new_tokens)

        return self._extract_sql(sql)

    def _connect_database(self, db_config):
        self.SGBD = db_config["SGBD"]

        if self.SGBD == "sqlite":
            db_path = db_config["db_path"]
            self.db_uri = f"sqlite:///{os.path.abspath(db_path)}"
        elif self.SGBD == "postgresql":
            user     = db_config.get("user", "postgres")
            password = db_config.get("password", "")
            host     = db_config.get("host", "localhost")
            port     = db_config.get("port", "5432")
            db_name  = db_config.get("db_name", "")
            self.db_uri = (
                f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
                "?sslmode=disable"
            )
        else:
            raise ValueError(f"SGBD não suportado: {self.SGBD}")

        old_engine = getattr(self, "engine", None)
        if old_engine is not None:
            old_engine.dispose()

        self.engine = create_engine(self.db_uri)

    def _set_model(self):
        if self.local_model:
            folder_name = self.model_id.replace("/", "-")
            self.model_path = os.path.join("./local_models/", folder_name)
            self._ensure_model_downloaded()
            self._load_local_pipeline()
        else:
            self.client = InferenceClient(
                model=self.model_id,
                token=self.hf_token,
            )
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

        tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            token=self.hf_token,
        )

        if tokenizer.pad_token_id is None:
            tokenizer.pad_token_id = tokenizer.eos_token_id

        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            token=self.hf_token,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )

        self.pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
        )


    def _infer_local(self, messages, max_new_tokens=512):
        outputs = self.pipe(
            messages,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            return_full_text=False,
        )
        return outputs[0]["generated_text"]

    def _infer_api(self, messages, max_new_tokens=512):
        response = self.client.chat_completion(
            messages=messages,
            max_tokens=max_new_tokens,
        )
        return response.choices[0].message.content


    def _build_prompt(self, schema: str, question: str):
        return [
            {
                "role": "system",
                "content": (
                    "You are an expert SQL assistant. "
                    "Given the database schema below, write a single valid SQL query "
                    "that answers the user's question. "
                    "Return ONLY the SQL query, without explanations or markdown.\n\n"
                    f"### Schema\n{schema}"
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ]

    def _get_schema(self) -> str:
        """Extrai o DDL simplificado do banco usando SQLAlchemy.

        Os identificadores (tabela e colunas) são gerados entre aspas duplas
        para preservar o case original. Sem as aspas, bancos case-sensitive
        (ex.: Postgres do `sih`, com colunas em maiúsculo) rebaixam os nomes
        para minúsculo e o modelo gera consultas com `column does not exist`.

        O resultado é cacheado por `db_uri`: para bancos fixos a inspeção roda
        uma única vez (evita inflar `tempo_geracao` com I/O do banco a cada
        pergunta); no Spider, `db_ids` repetidos reaproveitam o DDL.
        """
        cache = getattr(self, "_schema_cache", None)
        if cache is None:
            cache = self._schema_cache = {}

        if self.db_uri in cache:
            return cache[self.db_uri]

        inspector = inspect(self.engine)
        ddl_parts = []

        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            col_defs = ", ".join(
                f'"{col["name"]}" {col["type"]}' for col in columns
            )
            ddl_parts.append(f'CREATE TABLE "{table_name}" ({col_defs});')

        ddl = "\n".join(ddl_parts)
        cache[self.db_uri] = ddl
        return ddl

    def _extract_sql(self, raw_output: str) -> str:
        """
        Extrai a query SQL da saída crua do modelo.

        Lida com: blocos markdown (```sql, ```sqlite, ```postgresql, ou sem
        rótulo), prosa antes do SQL ("A consulta é: SELECT ..."), e SQL que não
        começa por uma palavra-chave reconhecida. Se nada casar, devolve a saída
        crua (último recurso).
        """
        if raw_output is None:
            return ""

        text = raw_output.strip()

        # 1) Se houver bloco de código cercado por ```, isola o conteúdo dele.
        fence = re.search(r"```(.*?)```", text, re.DOTALL)
        if fence:
            block = fence.group(1).strip()

            first_line, _, rest = block.partition("\n")
            if re.fullmatch(r"[A-Za-z0-9_+-]{1,15}", first_line.strip()):
                block = rest.strip()
            text = block.strip() or text

        # 2) Localiza o início de um statement SQL em qualquer posição.
        keywords = r"\b(WITH|SELECT|INSERT|UPDATE|DELETE|EXPLAIN|PRAGMA|CREATE|ALTER|DROP)\b"
        match = re.search(keywords, text, re.IGNORECASE)
        if match:
            return text[match.start():].strip()

        # 3) Fallback: devolve o que sobrou.
        return text
