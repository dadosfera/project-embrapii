---
table: REGIAO_DO_BRASIL
display_name: Regiões do Brasil
description: As cinco grandes regiões do Brasil (Norte, Nordeste, Centro-Oeste, Sudeste e Sul). Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, territorio
---

## O que é

Tabela de referência com as 5 regiões geográficas do Brasil (IBGE). Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Uma região do Brasil (5 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `codigo_da_regiao_do_brasil` | Código da região. |
| `regiao_do_brasil` | Nome da região. |

## Relacionamentos

- `unidade_federativa.regiao_do_brasil_id` -> `regiao_do_brasil`.

## Qualidade e observações

- Tabela de referência, estável.
