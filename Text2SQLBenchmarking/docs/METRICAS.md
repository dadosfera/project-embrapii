# Métricas

O contrato atual publica 13 conceitos métricos: Acurácia de Execução (EX) e 12
métricas adicionais persistidas por consulta. As definições abaixo descrevem a
implementação de `src/text2sql_metrics.py` e `src/metric_contract.py`.

## Regras gerais

- a SQL de referência e a SQL gerada são executadas uma vez;
- as métricas adicionais reutilizam os DataFrames e tempos já em memória;
- falha da referência torna as 12 métricas adicionais indisponíveis (`null`);
- se a referência executa e a gerada falha, métricas dependentes de resultado
  ficam em zero, enquanto métricas estruturais ainda podem ser calculadas;
- valores são persistidos por query; agregação ocorre posteriormente.

## Acurácia de Execução (EX)

EX não possui coluna própria redundante. É derivada de `execucoes_iguais`:

```text
EX = número de consultas com execucoes_iguais = true / total de consultas
```

`execucoes_iguais` só pode ser verdadeiro quando referência e gerada executam
com sucesso e seus DataFrames satisfazem a comparação oficial. Essa comparação
é sensível à ordem das linhas e ao limite implementado pelo executor.

## Métricas adicionais

### Soft F1 — `soft_f1`

Converte cada linha do resultado em tupla, usa o conjunto de linhas de cada
DataFrame e calcula F1 entre esses conjuntos. Ordem e multiplicidade de linhas
não participam. Dois conjuntos vazios retornam 1; somente um vazio retorna 0.

### Stats — `stats`

Compara média e desvio-padrão das colunas numéricas correspondentes, usando
tolerância absoluta `1e-2`. Retorna 1 somente quando todas as estatísticas são
compatíveis e 0 quando não são. Quantidades diferentes de colunas numéricas
retornam 0; se os dois recortes numéricos forem vazios, retorna 1.

### Similarity — `similarity`

Calcula similaridade de Jaccard entre os conjuntos de todos os valores das
células, convertidos para string. A posição do valor, a coluna e a
multiplicidade não entram nesse conjunto.

### Valid Efficiency Score — `ves`

Só produz valor positivo quando a comparação oficial de execução é correta e o
tempo gerado é maior que zero. Nesse caso, usa a razão entre tempo da referência
e tempo da gerada, limitada ao intervalo de 0 a 1. Caso contrário, retorna 0.

### Exact Match — `exact_match`

Faz parse com sqlglot e compara por igualdade os conjuntos extraídos de:
colunas, tabelas, agregações e condições suportadas. Retorna 1 quando todos os
componentes são iguais e 0 caso contrário.

### Component Match — `component_match`

Para cada categoria de componente SQL aplicável, calcula Jaccard entre os
conjuntos da referência e da gerada; o resultado é a média dessas categorias.
Categorias sem conteúdo em ambos os lados não entram na média.

### Structural Correctness — `structural_correctness`

Faz parse das duas consultas e compara as ASTs depois de anonimizar nomes de
tabelas e colunas. Mede igualdade da estrutura sintática abstraída dos
identificadores.

### Logical Form Accuracy — `logical_form_accuracy`

Compara as strings SQL após conversão para minúsculas e normalização de espaços.
Não faz equivalência semântica nem reordenação de cláusulas.

### Levenshtein Correctness — `leco`

Calcula a similaridade normalizada de Levenshtein diretamente entre as duas
strings SQL recebidas:

```text
1 - distância / maior comprimento
```

### Skeleton Correctness — `skeleton_correctness`

Extrai a sequência das palavras-chave estruturais implementadas (`SELECT`,
`FROM`, `WHERE`, `JOIN`, `GROUP`, `BY`, `ORDER`, `LIMIT` e `HAVING`) e testa a
igualdade das sequências.

### Partial Component Match F1 — `pcm_f1`

Calcula F1 por categoria aplicável de componentes SQL e retorna a média. Como
em Component Match, categorias vazias nos dois lados não participam.

### Query Affinity Score — `query_affinity_score`

Combina igualmente a similaridade textual LeCo e a Similarity dos resultados:

```text
QAS = 0,5 * LeCo + 0,5 * Similarity
```

A implementação possui tratamento explícito para resultado de referência
vazio.

## Falhas e valores nulos

| Situação | EX | Resultado-dependentes | Estruturais/textuais |
| --- | --- | --- | --- |
| referência falha | incorreta | `null` | `null` |
| referência executa, gerada falha | incorreta | 0 para Soft F1, Stats, Similarity, VES e QAS | calculadas quando a SQL permite |
| ambas executam | comparação oficial | calculadas | calculadas |

Zero é resultado científico; `null` significa indisponível. Não substitua
`null` por zero.

## Agregação

### EX e contagens

O denominador de EX é o total de linhas do experimento. O backend também
publica:

- `correct`: comparação correta;
- `incorrect_without_error`: ambas executaram, mas diferiram;
- `errors`: ao menos uma execução falhou;
- `timeouts`: subconjunto de `errors` identificado pelo padrão conservador do
  erro persistido da SQL gerada.

Timeouts não formam uma quarta partição da distribuição.

### Métricas adicionais

Para cada coluna, a agregação:

1. rejeita o artefato se houver valor não nulo e não finito;
2. descarta apenas `null`;
3. inclui zero;
4. calcula a média aritmética dos valores restantes;
5. publica como denominador a quantidade de valores usados.

Quando o denominador é zero, a métrica agregada é indisponível. O notebook usa
valores não nulos e finitos para suas médias e não recalcula a métrica por
query; pela interface, um não finito já torna o resultado inválido.

## Nomes canônicos

| Conceito | Código | Coluna Parquet |
| --- | --- | --- |
| Acurácia de Execução | `EX` | derivada de `execucoes_iguais` |
| Soft F1 | `Soft_F1` | `soft_f1` |
| Stats | `Stats` | `stats` |
| Similarity | `Similarity` | `similarity` |
| Valid Efficiency Score | `VES` | `ves` |
| Exact Match | `EM` | `exact_match` |
| Component Match | `CM` | `component_match` |
| Structural Correctness | `StCo` | `structural_correctness` |
| Logical Form Accuracy | `LFA` | `logical_form_accuracy` |
| Levenshtein Correctness | `LeCo` | `leco` |
| Skeleton Correctness | `SkCo` | `skeleton_correctness` |
| Partial Component Match F1 | `PCMF1` | `pcm_f1` |
| Query Affinity Score | `QAS` | `query_affinity_score` |

Os nomes de código e coluna são parte do contrato de artefatos. Não os renomeie
em uma análise sem uma migração metodológica explícita.
