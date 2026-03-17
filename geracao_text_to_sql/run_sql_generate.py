from src.premsqlAgente import PremSQLAgent
from src.vannaai import VannaAi
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

    args = parser.parse_args()
    
    db_name = args.db_name
    model_name = args.model_name
    biblioteca = args.biblioteca

    hf_token = os.getenv("HF_TOKEN")
    local_model = True

    db_config = get_db_config(db_name)
    model_id = get_model_id(model_name)
    context_path = get_context_path(db_name, biblioteca)

    if biblioteca == "PremSQLAgente":
        model = PremSQLAgent(db_config=db_config, model_id=model_id, hf_token=hf_token, local_model=local_model)
    elif (biblioteca == "vannaAi") or (biblioteca == "vannaAi_contexto"):
        model = VannaAi(db_config=db_config, model_id=model_id, hf_token=hf_token, local_model=local_model, doc_path=context_path)

    arquivo_queries = f'resources/queries/{db_name}/ground_truth.json'
    queries = pd.read_json(arquivo_queries)

    output_dir = f"resources/out/{db_name}/{model_id}/"
    os.makedirs(output_dir, exist_ok=True)

    tempo_geracao_total = 0
    queries_geradas = []

    for query in tqdm(queries.to_dict('records')):
        query_info = {}
        query_info["id"] = query["id"]
        query_info["question"] = query["question"]
        query_info["difficulty"] = query["difficulty"]
        if db_name == "sih_database":
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
    df_queries_geradas.to_parquet(f'{output_dir}/queries_geradas_{biblioteca}.parquet', index=False)

    exclude_permanence("vanna_storage")
    exclude_permanence("premsql")

if __name__ == "__main__":
    main()