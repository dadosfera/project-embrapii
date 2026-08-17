#!/bin/bash

# Raiz do repo = pasta acima de bash/. Funciona em qualquer servidor e no container.
cd "$(dirname "$0")/.." || exit 1

# DBS=("datasus")
DBS=("datasus" "sih_database")
# MODELOS=("Qwen2.5-Coder-14B-Instruct" "Qwen2.5-Coder-32B-Instruct" "Llama-3.1-8B-Instruct" "llama-3-sqlcoder-8b" "Qwen2.5-32B-Instruct")
MODELOS=("Qwen3-32B")
# BIBLIOTECAS=("rawModel" "vannaAi" "vannaAi_contexto")
# BIBLIOTECAS=("PremSQLAgente")
# BIBLIOTECAS=("vannaAi_exemplos", "vannaAi_contexto_exemplos")
# BIBLIOTECAS=("vannaAi_contexto_exemplos")
BIBLIOTECAS=("rawModel" "rawModel_exemplos")
# BIBLIOTECAS=("vannaAi_contexto" "vannaAi_exemplos" "vannaAi_contexto_exemplos")
# XiYanSQL (usar com modelos XiYanSQL-QwenCoder-*-2504). Sem vírgula entre itens!
# MODELOS=("XiYanSQL-QwenCoder-7B-2504")
# BIBLIOTECAS=("XiYanSQL" "XiYanSQL_contexto" "XiYanSQL_exemplos" "XiYanSQL_contexto_exemplos")

SEEDS=(42)

for model in "${MODELOS[@]}"; do
    for db in "${DBS[@]}"; do
        for lib in "${BIBLIOTECAS[@]}"; do
            for seed in "${SEEDS[@]}"; do
                
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