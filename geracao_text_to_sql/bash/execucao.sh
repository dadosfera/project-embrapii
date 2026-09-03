#!/bin/bash

WORKDIR="/home/fonseca/DDFR_geracao_text2sql/"
cd $WORKDIR

DBS=("sih_database" "datasus")
MODELOS=("Qwen2.5-Coder-7B-Instruct" "Qwen2.5-Coder-14B-Instruct" "Qwen2.5-Coder-32B-Instruct" "Llama-3.1-8B-Instruct" "llama-3-sqlcoder-8b")
BIBLIOTECAS=("vannaAi_contexto" "vannaAi_exemplos" "vannaAi_contexto_exemplos"  "PremSQLAgente" "rawModel")
# MODELOS=("XiYanSQL-QwenCoder-7B-2504")
# BIBLIOTECAS=("XiYanSQL" "XiYanSQL_contexto" "XiYanSQL_exemplos" "XiYanSQL_contexto_exemplos")

SEEDS=(42)

for seed in "${SEEDS[@]}"; do
    for model in "${MODELOS[@]}"; do
        for db in "${DBS[@]}"; do
            for lib in "${BIBLIOTECAS[@]}"; do
                
                echo "-------------------------------------------------------"
                echo "Executando: DB=$db | Model=$model | Lib=$lib | Seed=$seed"
                echo "-------------------------------------------------------"

                python3 run_sql_execution.py \
                    --db_name "$db" \
                    --model_name "$model" \
                    --biblioteca "$lib" \
                    --random_seed "$seed"

            done
        done
    done
done

echo "FIM!"