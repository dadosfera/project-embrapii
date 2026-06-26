from src.premsqlAgente import PremSQLAgent
from src.rawmodel import RawModel
from src.vannaai import VannaAi
from src.xiyansql import XiYanSQL
from dotenv import load_dotenv
from src.utilitis import *
from tqdm import tqdm
import pandas as pd
import argparse
import time
import os

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--db_name", type=str, required=True, help="Nome do banco de dados (ex: datasus)")
    parser.add_argument("--model_name", type=str, required=True, help="Nome do modelo (ex: llama3, mistral)")
    parser.add_argument("--biblioteca", type=str, default="vanna", help="Biblioteca utilizada (padrão: vanna)")
    parser.add_argument("--random_seed", type=int, default=42, help="Semente de aleatoriedade (padrão: 42)")

    args = parser.parse_args()
    
    db_name = args.db_name
    model_name = args.model_name
    biblioteca = args.biblioteca
    random_seed = args.random_seed

    load_dotenv()
    hf_token = os.getenv("HF_TOKEN")
    local_model = True

    set_seed(random_seed)

    db_config, ground_truth_name = get_db_config(db_name)
    model_id = get_model_id(model_name)
    context_path = get_context_path(db_name, biblioteca)
    examples_path = get_examples_path(db_name, biblioteca)


    if biblioteca == "PremSQLAgente":
        model = PremSQLAgent(db_config=db_config, model_id=model_id, hf_token=hf_token, local_model=local_model)
    elif (biblioteca == "vannaAi") or (biblioteca == "vannaAi_contexto") or (biblioteca == "vannaAi_exemplos") or (biblioteca == "vannaAi_contexto_exemplos"):
        model = VannaAi(db_config=db_config, model_id=model_id, hf_token=hf_token, local_model=local_model, doc_path=context_path, examples_path=examples_path)
    elif biblioteca == "rawModel":
        model = RawModel(db_config=db_config, model_id=model_id, hf_token=hf_token, local_model=local_model)
    elif biblioteca in ("XiYanSQL", "XiYanSQL_contexto", "XiYanSQL_exemplos", "XiYanSQL_contexto_exemplos"):
        model = XiYanSQL(db_config=db_config, model_id=model_id, hf_token=hf_token, local_model=local_model, doc_path=context_path, examples_path=examples_path)

    arquivo_queries = f'datasets/{db_name}/queries/pt/{ground_truth_name}.json'

    queries = pd.read_json(arquivo_queries)

    output_dir = f"resources/out/{db_name}/{model_id}/"
    os.makedirs(output_dir, exist_ok=True)

    tempo_geracao_total = 0
    queries_geradas = []

    id = 0
    for query in tqdm(queries.to_dict('records')):
        query_info = {}
        
        query_info["id"] = query["id"]
        query_info["question"] = query["question"]
        if db_name in ["sih_database"]:
            query_info["sql_ground_truth"] = query["query"]
        elif db_name == "datasus":
            query_info["sql_ground_truth"] = query["sql"]

        tempo_geracao_inicio = time.time()

        saida_gerada = model.generate_query(query["question"])

        tempo_geracao_fim = time.time()
        tempo_geracao = tempo_geracao_fim - tempo_geracao_inicio

        query_info["sql_generated"] = saida_gerada
        query_info["tempo_geracao"] = tempo_geracao

        queries_geradas.append(query_info)
        tempo_geracao_total += tempo_geracao


    print(f"Tempo total de geração: {tempo_geracao_total}")

    df_queries_geradas = pd.DataFrame(queries_geradas)
    df_queries_geradas.to_parquet(f'{output_dir}/queries_geradas_{biblioteca}_{random_seed}.parquet', index=False)

    exclude_permanence("vanna_storage")
    exclude_permanence("premsql")

if __name__ == "__main__":
    main()