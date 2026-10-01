---
table: REGIAO_DE_SAUDE
display_name: Regiões de saúde
description: Regiões de saúde (agrupamentos de municípios para planejamento do SUS): código, nome e macrorregião. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, territorio
---

## O que é

Cadastro das 439 regiões de saúde, cada uma ligada a uma macrorregião de saúde. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Uma região de saúde (439 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `codigo_da_regiao_de_saude` | Código da região de saúde. |
| `regiao_de_saude` | Nome da região. |
| `macrorregiao_de_saude_id` | Macrorregião a que pertence. |

## Relacionamentos

- `regiao_de_saude.macrorregiao_de_saude_id` -> `macrorregiao_de_saude`.
- `municipio.regiao_de_saude_id` -> `regiao_de_saude`.

## Qualidade e observações

- Os campos de ligação (`..._id`) estão como texto nesta tabela; ao fazer junções, confira os tipos.
