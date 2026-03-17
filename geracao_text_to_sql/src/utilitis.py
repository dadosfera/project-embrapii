import torch

def set_seed(seed=42):
    import random
    import numpy as np
    import os
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def get_context_path(db_name, biblioteca):
    if db_name == "datasus" and biblioteca == "vannaAi_contexto":
        context_path = "resources/queries/datasus/datasus_documentation.md"
    elif db_name == "sih_database" and biblioteca == "vannaAi_contexto":
        context_path = "resources/queries/sih_database/sih_documentation.md"
    else:
        context_path = None
    return context_path

def get_db_config(db_name):

    if db_name == "datasus":
        DB_CONFIG = {
            'SGBD': "postgresql",
            'user': "datalake_user",
            'password': "senha123",
            'host': "localhost",  
            'port': "5433",       
            'db_name': "datalake_db2"
        }
    elif db_name == "sih_database":
        DB_CONFIG = {
            'SGBD': "postgresql",
            'user': 'postgres',
            'password': '1234',
            'host': 'localhost',
            'port': '5432',
            'db_name': 'sih_rs_test'
        }
    
    return DB_CONFIG

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
    return model_id

def exclude_permanence(path):
    import shutil
    import os

    if os.path.exists(path):
        shutil.rmtree(path)