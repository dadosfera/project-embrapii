# Pipeline científico e scripts

## Ordem do pipeline

```text
1. geração de SQL
        |
        v
2. execução e comparação
        |
        v
3. cálculo e persistência das métricas
        |
        v
4. análise dos Parquets executados
```

As etapas 2 e 3 ocorrem na mesma chamada de `run_sql_execution.py`. As 12
métricas adicionais usam os resultados já em memória; não executam novamente
a SQL gerada nem a referência.

Todos os comandos desta página executam no container backend. Eles são workload
científico real: podem acessar banco, usar GPU, baixar modelo e gravar ou
sobrescrever o Parquet da combinação. Não os use para smoke test.

## Preparação do ambiente Docker

Na raiz:

```bash
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export PROJECT_ROOT="$PWD"
```

Os scripts manuais não participam do lock da API. Antes de usá-los, confirme
que nenhum Chat ou Benchmark está em andamento e pare o backend:

```bash
docker compose stop backend
```

Ao terminar a sequência pretendida:

```bash
docker compose start backend
```

## `run_sql_generate.py`

### Finalidade

Lê o ground truth, carrega a biblioteca/modelo, gera uma SQL por pergunta e
grava o Parquet de geração no fim da rodada.

### Argumentos

| Argumento | Obrigatório | Significado |
| --- | --- | --- |
| `--db_name` | sim | ID da base |
| `--model_name` | sim | nome do registry local, não o ID Hugging Face completo |
| `--biblioteca` | recomendado sempre | token exato da biblioteca/contexto |
| `--random_seed` | não | seed inteira; padrão 42 |

Embora o parser possua um valor histórico padrão para `--biblioteca`, sempre
informe um token válido da tabela abaixo.

### Exemplo

```bash
docker compose run --rm backend \
  python3 run_sql_generate.py \
  --db_name sih_database \
  --model_name Qwen2.5-Coder-7B-Instruct \
  --biblioteca rawModel \
  --random_seed 42
```

### Entradas e saída

- ground truth correspondente à base;
- documentação/exemplos quando o token solicitar contexto;
- modelo em `local_models/` ou Hugging Face;
- banco quando a biblioteca precisar inspecionar schema ou exemplos;
- saída em
  `resources/out/<base>/<model_id>/queries_geradas_<token>_<seed>.parquet`.

O arquivo é gravado apenas no fim. O script não possui resume/checkpoint.

## `run_sql_execution.py`

### Finalidade

Lê o Parquet de geração, executa a SQL de referência e a SQL gerada, compara os
DataFrames, calcula EX e as 12 métricas adicionais e grava o Parquet executado.

### Argumentos

Os quatro argumentos são os mesmos da geração e devem identificar exatamente o
arquivo produzido na etapa anterior.

### Exemplo

```bash
docker compose run --rm backend \
  python3 run_sql_execution.py \
  --db_name sih_database \
  --model_name Qwen2.5-Coder-7B-Instruct \
  --biblioteca rawModel \
  --random_seed 42
```

### Entradas e saída

- Parquet de geração da mesma identidade;
- PostgreSQL correspondente;
- saída em
  `resources/out/<base>/<model_id>/queries_geradas_<token>_<seed>_executado.parquet`.

O timeout da SQL gerada é o maior valor entre 30 segundos e dez vezes o tempo
da referência. A comparação oficial continua sensível à ordem das linhas e ao
limite operacional implementado pelo executor. Alterar isso seria mudança
metodológica.

## Tokens de biblioteca e contexto

| Biblioteca | Contexto | `--biblioteca` |
| --- | --- | --- |
| RawModel | padrão | `rawModel` |
| RawModel | exemplos | `rawModel_exemplos` |
| PremSQLAgent | padrão | `PremSQLAgente` |
| VannaAI | sem contexto | `vannaAi` |
| VannaAI | documentação | `vannaAi_contexto` |
| VannaAI | exemplos | `vannaAi_exemplos` |
| VannaAI | documentação + exemplos | `vannaAi_contexto_exemplos` |
| XiYanSQL | sem contexto | `XiYanSQL` |
| XiYanSQL | documentação | `XiYanSQL_contexto` |
| XiYanSQL | exemplos | `XiYanSQL_exemplos` |
| XiYanSQL | documentação + exemplos | `XiYanSQL_contexto_exemplos` |

Use modelos XiYan apenas com tokens XiYan. Consulte a compatibilidade completa
em [Modelos, bibliotecas, contextos e seeds](MODELOS_BIBLIOTECAS_CONTEXTOS.md).

## Wrappers Bash

### `bash/geracao.sh`

Percorre os arrays `DBS`, `MODELOS`, `BIBLIOTECAS` e `SEEDS` e chama
`run_sql_generate.py` para cada produto cartesiano.

```bash
docker compose run --rm backend bash bash/geracao.sh
```

### `bash/execucao.sh`

Percorre os mesmos quatro eixos e chama `run_sql_execution.py`.

```bash
docker compose run --rm backend bash bash/execucao.sh
```

Os wrappers não aceitam argumentos de linha de comando. Revise conscientemente
os arrays no arquivo **antes do build da imagem**; itens Bash são separados por
espaço, nunca por vírgula. Se o arquivo local mudar, refaça o build para que a
cópia da imagem seja atualizada. Para uma única configuração, prefira as CLIs
explícitas, que tornam a identidade visível no comando.

## Bases suportadas pelo pipeline

| `db_name` | Engine | Ground truth usada |
| --- | --- | --- |
| `datasus` | PostgreSQL | `datasets/datasus/queries/pt/benchmark_curated.json` |
| `sih_database` | PostgreSQL | `datasets/sih_database/queries/pt/ground_truth.json` |

Este entregável não inclui PM-USP, Spider, bancos SQLite nem seus arquivos
auxiliares. Embora permaneçam ramificações históricas de compatibilidade no
código, essas bases não compõem um fluxo executável ou suportado neste pacote.

## Executar uma etapa isoladamente

- geração pode rodar sem execução, produzindo estado `generation_only`;
- execução exige o Parquet de geração da mesma identidade;
- análise exige Parquets executados com o contrato atual de métricas;
- remover a geração e manter apenas o executado é um estado inválido para a
  interface.

## Notebook de análise

`run_analise.ipynb` é a quarta etapa. Ele lê Parquets executados, deriva EX de
`execucoes_iguais` e agrega as 12 colunas adicionais usando seus denominadores
não nulos. Não reimplementa as fórmulas por consulta e não grava Parquets.

As células atuais contêm conjuntos explícitos de bases, modelos, bibliotecas e
seed; revise a seleção antes de executar. A operação via container está em
[Análise e testes](ANALISE_E_TESTES.md).

## Outros scripts e notebooks

Não existem outros arquivos `run_*.py` no projeto. Notebooks auxiliares de
dataset e helpers de obtenção de dados não fazem parte do entregável. A
ferramenta opcional `interface/tools/runtime_switch_smoke.py` é documentada em
[Análise e testes](ANALISE_E_TESTES.md) e não pertence ao pipeline científico.
