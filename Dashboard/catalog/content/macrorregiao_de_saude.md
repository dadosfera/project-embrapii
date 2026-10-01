---
table: MACRORREGIAO_DE_SAUDE
display_name: Macrorregiões de saúde
description: Macrorregiões de saúde (agrupamentos de regiões de saúde): código, nome e UF. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, territorio
---

## O que é

Cadastro das 121 macrorregiões de saúde, cada uma ligada a uma unidade federativa. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Uma macrorregião de saúde (121 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `codigo_macrorregiao_de_saude` | Código da macrorregião. |
| `macrorregiao_de_saude` | Nome da macrorregião. |
| `unidade_federativa_id` | UF a que pertence. |

## Relacionamentos

- `macrorregiao_de_saude.unidade_federativa_id` -> `unidade_federativa`.
- `regiao_de_saude.macrorregiao_de_saude_id` -> `macrorregiao_de_saude`.

## Qualidade e observações

- Os campos de ligação (`..._id`) estão como texto nesta tabela; ao fazer junções, confira os tipos.
