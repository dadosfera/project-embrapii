from src.executor import sqlExecutor
from src.metric_contract import ADDITIONAL_METRIC_COLUMNS
from src.text2sql_metrics import calculate_additional_metrics, dialect_for_sgbd
from sqlalchemy import text
from src.utilitis import *
from tqdm import tqdm
import pandas as pd
import argparse
import time
import os


def execute_queries(queries_geradas, executor, db_name, *, progress=tqdm):
    """Executa cada SQL uma vez e materializa EX e as métricas adicionais."""

    queries_executadas = queries_geradas.copy()
    is_spider = db_name in ["spider-dev", "spider-test"]
    lista_ids = queries_executadas.index if is_spider else queries_executadas['id']

    queries_executadas['tempo_execucao_ground_truth'] = None
    queries_executadas['execucao_correta_ground_truth'] = None
    queries_executadas['tempo_execucao_generated'] = None
    queries_executadas['execucao_correta_generated'] = None
    queries_executadas['erro_execucao_generated'] = None
    queries_executadas['execucoes_iguais'] = None
    for column in ADDITIONAL_METRIC_COLUMNS:
        queries_executadas[column] = pd.Series(
            pd.NA,
            index=queries_executadas.index,
            dtype="Float64",
        )

    tempo_execucao_total = 0

    for idx in progress(lista_ids):
        if is_spider:
            row = queries_executadas.iloc[idx]
            banco = "database" if db_name == "spider-dev" else "test_database"
            db_config = {
                'SGBD': "sqlite",
                'db_path': f"datasets/spider-pt/spider_data/{banco}/{row['db_id']}/{row['db_id']}.sqlite"
            }
            executor.connect(db_config)
            filter_mask = queries_executadas.index == idx
        else:
            filter_mask = queries_executadas['id'] == idx

        sql_ground_truth = queries_executadas.loc[
            filter_mask,
            "sql_ground_truth",
        ].values[0]
        sql_generated = queries_executadas.loc[
            filter_mask,
            "sql_generated",
        ].values[0]

        # Execucao SQL ground truth: este e o unico ponto de execucao da GT.
        tempo_execucao_ground_truth_inicio = time.time()
        out_ground_truth = executor.execute_query(text(sql_ground_truth))
        tempo_execucao_ground_truth_fim = time.time()
        tempo_execucao_ground_truth = (
            tempo_execucao_ground_truth_fim - tempo_execucao_ground_truth_inicio
        )

        queries_executadas.loc[
            filter_mask,
            "tempo_execucao_ground_truth",
        ] = tempo_execucao_ground_truth

        if isinstance(out_ground_truth, str):
            execucao_correta_ground_truth = False
        else:
            execucao_correta_ground_truth = True
        queries_executadas.loc[
            filter_mask,
            "execucao_correta_ground_truth",
        ] = execucao_correta_ground_truth
        tempo_execucao_total += tempo_execucao_ground_truth

        # Execucao SQL gerada: este e o unico ponto de execucao da predicao.
        tempo_execucao_generated_inicio = time.time()
        out_generated = executor.execute_query(
            text(sql_generated),
            t=max(30, 10 * tempo_execucao_ground_truth),
        )
        tempo_execucao_generated_fim = time.time()
        tempo_execucao_generated = (
            tempo_execucao_generated_fim - tempo_execucao_generated_inicio
        )

        queries_executadas.loc[
            filter_mask,
            "tempo_execucao_generated",
        ] = tempo_execucao_generated

        if isinstance(out_generated, str):
            execucao_correta_generated = False
            queries_executadas.loc[
                filter_mask,
                "erro_execucao_generated",
            ] = out_generated
        else:
            execucao_correta_generated = True
        queries_executadas.loc[
            filter_mask,
            "execucao_correta_generated",
        ] = execucao_correta_generated
        tempo_execucao_total += tempo_execucao_generated

        # EX oficial permanece exatamente baseada na comparacao consolidada.
        if (execucao_correta_generated == False) or (execucao_correta_ground_truth == False):
            queries_executadas.loc[filter_mask, "execucoes_iguais"] = False
        else:
            queries_executadas.loc[filter_mask, "execucoes_iguais"] = executor._compare_dataframes(
                out_generated, out_ground_truth
            )

        execution_equal = bool(
            queries_executadas.loc[filter_mask, "execucoes_iguais"].values[0]
        )
        try:
            metric_values = calculate_additional_metrics(
                sql_pred=sql_generated,
                sql_gold=sql_ground_truth,
                df_pred=out_generated if execucao_correta_generated else None,
                df_gold=(
                    out_ground_truth if execucao_correta_ground_truth else None
                ),
                t_gt=tempo_execucao_ground_truth,
                t_generated=tempo_execucao_generated,
                ground_truth_succeeded=execucao_correta_ground_truth,
                generated_succeeded=execucao_correta_generated,
                execution_equal=execution_equal,
                dialect=dialect_for_sgbd(executor.SGBD),
            )
        except Exception as exc:
            raise RuntimeError(
                "Falha interna ao calcular as metricas adicionais."
            ) from exc

        for column, value in metric_values.items():
            queries_executadas.loc[filter_mask, column] = value

    return queries_executadas, tempo_execucao_total


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

    model_id = get_model_id(model_name)

    is_spider = db_name in ["spider-dev", "spider-test"]

    if is_spider:
        executor = sqlExecutor()
    else:
        db_config, _ = get_db_config(db_name)
        executor = sqlExecutor(db_config=db_config)

    input_file = f"resources/out/{db_name}/{model_id}/queries_geradas_{biblioteca}_{random_seed}.parquet"
    queries_geradas = pd.read_parquet(f'{input_file}')

    n_queries = queries_geradas.shape[0]
    print(n_queries)
    queries_geradas, tempo_execucao_total = execute_queries(
        queries_geradas,
        executor,
        db_name,
    )

    print(f"Tempo total de execução (s): {tempo_execucao_total}")

    outputpath = input_file.replace(".parquet", f"_executado.parquet")
    queries_geradas.to_parquet(f'{outputpath}', index=False)


if __name__ == "__main__":
    main()
