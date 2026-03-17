from src.executor import sqlExecutor
from sqlalchemy import text
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

    db_config = get_db_config(db_name)
    model_id = get_model_id(model_name)

    executor = sqlExecutor(db_config=db_config)

    input_file = f"resources/out/{db_name}/{model_id}/queries_geradas_{biblioteca}.parquet"

    queries_geradas = pd.read_parquet(f'{input_file}')

    lista_ids = queries_geradas['id']
    n_queries = queries_geradas.shape[0]
    print(n_queries)
    print(queries_geradas['difficulty'].value_counts())

    queries_geradas['tempo_execucao_ground_truth'] = None
    queries_geradas['execucao_correta_ground_truth'] = None
    queries_geradas['tempo_execucao_generated'] = None
    queries_geradas['execucao_correta_generated'] = None
    queries_geradas['erro_execucao_generated'] = None
    queries_geradas['execucoes_iguais'] = None

    tempo_execucao_total = 0

    for query_idx in tqdm(lista_ids):

        # Execução sql ground truth

        tempo_execucao_ground_truth_inicio = time.time()

        out_ground_truth = executor.execute_query(text(queries_geradas.loc[queries_geradas['id'] == query_idx, "sql_ground_truth"].values[0]))

        tempo_execucao_ground_truth_fim = time.time()
        tempo_execucao_ground_truth = tempo_execucao_ground_truth_fim - tempo_execucao_ground_truth_inicio

        queries_geradas.loc[queries_geradas['id'] == query_idx, "tempo_execucao_ground_truth"] = tempo_execucao_ground_truth
        
        if isinstance(out_ground_truth, str):
            execucao_correta_ground_truth = False # erro na execução do df
        else:
            execucao_correta_ground_truth = True
        queries_geradas.loc[queries_geradas['id'] == query_idx, "execucao_correta_ground_truth"] = execucao_correta_ground_truth
        tempo_execucao_total += tempo_execucao_ground_truth

        # Execução sql gerado

        tempo_execucao_generated_inicio = time.time()

        out_generated = executor.execute_query(text(queries_geradas.loc[queries_geradas['id'] == query_idx, "sql_generated"].values[0]), t=10*tempo_execucao_ground_truth)

        tempo_execucao_generated_fim = time.time()
        tempo_execucao_generated = tempo_execucao_generated_fim - tempo_execucao_generated_inicio

        queries_geradas.loc[queries_geradas['id'] == query_idx, "tempo_execucao_generated"] = tempo_execucao_generated
        if isinstance(out_generated, str):
            execucao_correta_generated = False
            queries_geradas.loc[queries_geradas['id'] == query_idx, "erro_execucao_generated"] = out_generated
        else:
            execucao_correta_generated = True
        queries_geradas.loc[queries_geradas['id'] == query_idx, "execucao_correta_generated"] = execucao_correta_generated
        tempo_execucao_total += tempo_execucao_generated

        if (execucao_correta_generated == False) or (execucao_correta_ground_truth == False):
            queries_geradas.loc[queries_geradas['id'] == query_idx, "execucoes_iguais"] = False
        else:
            queries_geradas.loc[queries_geradas['id'] == query_idx, "execucoes_iguais"] = executor._compare_dataframes(out_generated, out_ground_truth)

    print(f"Tempo total de execução (s): {tempo_execucao_total}")

    outputpath = input_file.replace(".parquet", f"_executado.parquet")
    queries_geradas.to_parquet(f'{outputpath}', index=False)


if __name__ == "__main__":
    main()