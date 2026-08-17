# Artefatos e resultados

## Diretório de saída

Resultados científicos ficam em `resources/out/`, organizados por base e ID do
modelo:

```text
resources/out/
└── <base>/
    └── <model_id>/
        ├── queries_geradas_<token>_<seed>.parquet
        ├── queries_geradas_<token>_<seed>_executado.parquet
        └── history/
            └── <YYYYMMDD_HHMMSS>/
```

Se `model_id` contém barra, ela cria subdiretórios, como `Qwen/...`.

## Identidade e nomes

A identidade completa combina:

- base;
- biblioteca;
- modelo;
- contexto;
- seed.

Biblioteca e contexto são codificados no token legado do arquivo. Consulte a
tabela em [Benchmark](BENCHMARK.md). A seed aparece como inteiro no nome.

## Parquet de geração

Colunas obrigatórias:

| Coluna | Significado |
| --- | --- |
| `id` | identificador da pergunta |
| `question` | pergunta em linguagem natural |
| `sql_ground_truth` | SQL de referência |
| `sql_generated` | SQL produzida pelo modelo |
| `tempo_geracao` | tempo de geração em segundos |

O arquivo só é gravado quando a rodada de geração termina. Não existe
checkpoint parcial oficial.

## Parquet executado

Mantém as colunas de geração e adiciona seis campos operacionais:

| Coluna | Significado |
| --- | --- |
| `tempo_execucao_ground_truth` | tempo da referência |
| `execucao_correta_ground_truth` | sucesso da referência |
| `tempo_execucao_generated` | tempo da SQL gerada |
| `execucao_correta_generated` | sucesso da SQL gerada |
| `erro_execucao_generated` | mensagem histórica da falha gerada, quando houver |
| `execucoes_iguais` | resultado da comparação oficial |

Também contém as 12 colunas adicionais:

```text
soft_f1
stats
similarity
ves
exact_match
component_match
structural_correctness
logical_form_accuracy
leco
skeleton_correctness
pcm_f1
query_affinity_score
```

Nas duas bases entregues, isso totaliza 23 colunas. EX é derivada de
`execucoes_iguais` e não ocupa coluna própria.

## Validação dos artefatos

A interface valida presença, tipo e coerência sem alterar os arquivos. Estados:

| Estado | Condição |
| --- | --- |
| `not_started` | nenhum dos dois arquivos válidos existe |
| `generation_only` | apenas geração válida existe |
| `complete` | geração e execução válidas existem |
| `invalid_result` | schema, combinação ou semântica não atende ao contrato |

Exemplos de invalidade incluem execução sem geração, coluna obrigatória
ausente, tipo incompatível e valor métrico não finito. Um executado legado sem
as 12 colunas não é migrado ou preenchido automaticamente.

## Reexecução e `history/`

Reexecução de um estado completo exige confirmação. Antes da nova rodada, o
serviço arquiva os Parquets ativos em:

```text
resources/out/<base>/<model_id>/history/<YYYYMMDD_HHMMSS>/
```

Os nomes originais são preservados. Em colisão de timestamp, é usado um sufixo.
O serviço valida que os arquivos são regulares, pertencem à identidade esperada
e permanecem no mesmo filesystem para a movimentação. Se o preflight ou o
arquivamento falhar, a nova execução não começa. Em falha parcial, o serviço
tenta rollback.

Versões em `history/` não são selecionáveis pela interface e não são removidas
automaticamente.

## Confirmação de reexecução

A intenção de confirmação:

- é opaca e não contém o conteúdo dos Parquets;
- fica em memória;
- expira em 300 segundos;
- é de uso único;
- vincula identidade e snapshots exatos dos dois caminhos.

Mudança de tamanho, mtime ou hash depois da confirmação produz
`REEXECUTION_STATE_CHANGED` e exige nova inspeção.

## Snapshots

O Benchmark registra metadata de cada artefato:

- caminho relativo;
- existência;
- tamanho;
- tempo de modificação;
- SHA-256.

O conteúdo científico não é copiado para o journal.

## Journal

O arquivo operacional é:

```text
interface/.runtime/benchmark-journal.sqlite3
```

Ele guarda snapshots imutáveis dos jobs e permite que a API publique o job
ativo/mais recente após recarregar a página. No startup, jobs não terminais são
reconciliados com os snapshots dos artefatos.

O journal não faz resume do subprocesso. Sem evidência de conclusão, um job
pode terminar como `interrupted`. Ausência do arquivo no primeiro uso é
suportada; o backend o cria. Não edite, remova ou execute manutenção SQLite
durante operação.

## Outros estados persistentes

| Caminho | Conteúdo | Natureza |
| --- | --- | --- |
| `interface/.runtime/adapters/` | workspaces e links de runtime | efêmero/recriável, com lifecycle controlado |
| `interface/.runtime/chroma-cache/` | embedding/cache Chroma da VannaAI | persistente e reutilizável |
| `local_models/` | pesos Hugging Face | persistente e potencialmente grande |
| `vanna_storage/`, `premsql/` | workspaces de scripts batch | temporários |

## Tempos agregados

A interface soma os valores persistidos para apresentar:

- geração;
- execução da referência;
- execução da SQL gerada;
- execução total;
- total registrado.

O total registrado é soma de campos do Parquet e não representa duração de
parede do job.

## Preservação

- não edite Parquets manualmente;
- não substitua `null` por zero;
- não mova arquivos durante geração, execução ou arquivamento;
- não use `resources/out/` como diretório de testes;
- preserve `history/` quando houver valor científico ou de auditoria;
- faça backup de resultados necessários antes de manutenção de storage.
