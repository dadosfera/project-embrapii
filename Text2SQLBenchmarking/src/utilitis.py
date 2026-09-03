import os

import torch


_POSTGRES_ENV_FIELDS = {
    "HOST": "host",
    "PORT": "port",
    "NAME": "db_name",
    "USER": "user",
    "PASSWORD": "password",
}

_POSTGRES_ENV_PREFIXES = {
    "datasus": "DATASUS_DB",
    "sih_database": "SIH_DATABASE_DB",
}


def _apply_postgres_env_overrides(db_name, db_config):
    """Aplica somente campos PostgreSQL explicitamente configurados no ambiente."""

    prefix = _POSTGRES_ENV_PREFIXES.get(db_name)
    if prefix is None:
        return db_config

    overridden = dict(db_config)
    for suffix, field in _POSTGRES_ENV_FIELDS.items():
        variable = f"{prefix}_{suffix}"
        if variable in os.environ:
            overridden[field] = os.environ[variable]
    return overridden

def set_seed(seed=42):
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

# Bibliotecas que usam DOCUMENTAÇÃO (contexto): variantes "_contexto*".
_BIBLIOTECAS_CONTEXTO = [
    "vannaAi_contexto", "vannaAi_contexto_exemplos",
    "XiYanSQL_contexto", "XiYanSQL_contexto_exemplos",
]
# Bibliotecas que usam EXEMPLOS few-shot: variantes "_exemplos*".
_BIBLIOTECAS_EXEMPLOS = [
    "rawModel_exemplos",
    "vannaAi_exemplos", "vannaAi_contexto_exemplos",
    "XiYanSQL_exemplos", "XiYanSQL_contexto_exemplos",
]

def get_context_path(db_name, biblioteca):
    if biblioteca not in _BIBLIOTECAS_CONTEXTO:
        return None
    if db_name == "datasus":
        return "datasets/datasus/datasus_documentation_resumida.md"
    elif db_name == "sih_database":
        return "datasets/sih_database/sih_documentation_resumida.md"
    return None

def get_examples_path(db_name, biblioteca):
    if biblioteca not in _BIBLIOTECAS_EXEMPLOS:
        return None
    if db_name == "datasus":
        return "datasets/datasus/consultas_exemplo_reduzido.json"
    elif db_name == "sih_database":
        return "datasets/sih_database/exemplos.json"
    return None

def get_db_config(db_name):

    if db_name == "datasus":
        DB_CONFIG = {
            'SGBD': "postgresql",
            'user': "datalake_user",
            'password': "senha123",
            'host': "localhost",  
            'port': "5433",       
            'db_name': "datalake_db2",
        }
        ground_truth_name = "benchmark_curated"
    elif db_name == "sih_database":
        DB_CONFIG = {
            'SGBD': "postgresql",
            'user': 'postgres',
            'password': '1234',
            'host': 'localhost',
            'port': '5432',
            'db_name': 'sih_rs_test',
        }
        ground_truth_name = "ground_truth"
    elif db_name == "pm-USP":
        DB_CONFIG = {
            'SGBD': "sqlite",
            'db_path': "datasets/pm-USP/pm-usp_data/event_log.db",
        }
        ground_truth_name = "dev"
    elif db_name == "spider-dev":
        DB_CONFIG = None
        ground_truth_name = "dev"
    elif db_name == "spider-test":
        DB_CONFIG = None
        ground_truth_name = "test"
    else:
        DB_CONFIG = None
        ground_truth_name = None

    if DB_CONFIG is not None and DB_CONFIG.get("SGBD") == "postgresql":
        DB_CONFIG = _apply_postgres_env_overrides(db_name, DB_CONFIG)

    return DB_CONFIG, ground_truth_name

def get_model_id(model_name):

    
    if   model_name == "Qwen2.5-Coder-7B-Instruct":
        model_id = "Qwen/Qwen2.5-Coder-7B-Instruct"
    elif model_name == "Qwen2.5-Coder-14B-Instruct":
        model_id = "Qwen/Qwen2.5-Coder-14B-Instruct"
    elif model_name == "Qwen2.5-Coder-32B-Instruct":
        model_id = "Qwen/Qwen2.5-Coder-32B-Instruct"
    elif model_name == "Llama-3.1-8B-Instruct":
        model_id = "meta-llama/Llama-3.1-8B-Instruct"
    elif model_name == "llama-3-sqlcoder-8b":
        model_id = "defog/llama-3-sqlcoder-8b"
    elif model_name == "Qwen2.5-32B-Instruct":
        model_id = "Qwen/Qwen2.5-32B-Instruct"
    elif model_name == "sabia-7b":
        model_id = "maritaca-ai/sabia-7b"
    # Modelos fine-tunados XiYanSQL-QwenCoder (versão 2504, a mais recente).
    # Versões alternativas disponíveis: 3B/7B/14B-2502 e 32B-2412.
    elif model_name == "XiYanSQL-QwenCoder-3B-2504":
        model_id = "XGenerationLab/XiYanSQL-QwenCoder-3B-2504"
    elif model_name == "XiYanSQL-QwenCoder-7B-2504":
        model_id = "XGenerationLab/XiYanSQL-QwenCoder-7B-2504"
    elif model_name == "XiYanSQL-QwenCoder-14B-2504":
        model_id = "XGenerationLab/XiYanSQL-QwenCoder-14B-2504"
    elif model_name == "XiYanSQL-QwenCoder-32B-2504":
        model_id = "XGenerationLab/XiYanSQL-QwenCoder-32B-2504"
    # Modelos Qwen3 (atenção: têm modo "thinking" ligado por padrão; exigem
    # transformers >= 4.57.1 no caso do Qwen3.6-35B-A3B, arquitetura qwen3_5_moe).
    elif model_name == "Qwen3-32B":
        model_id = "Qwen/Qwen3-32B"
    elif model_name == "Qwen3.6-35B-A3B":
        model_id = "Qwen/Qwen3.6-35B-A3B"
    else:
        raise ValueError(
            f"model_name desconhecido: '{model_name}'. "
            "Registre-o em get_model_id (src/utilitis.py)."
        )
    return model_id

def exclude_permanence(path):
    import shutil
    import os

    if os.path.exists(path):
        shutil.rmtree(path)
