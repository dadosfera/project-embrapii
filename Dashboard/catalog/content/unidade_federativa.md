---
table: UNIDADE_FEDERATIVA
display_name: Unidades federativas
description: Os 27 estados e o Distrito Federal: código, nome, sigla e região do Brasil. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, territorio
---

## O que é

Cadastro das 27 unidades federativas (IBGE), ligadas à região do Brasil. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Uma unidade federativa (27 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `codigo_da_unidade_federativa` | Código da UF (IBGE). |
| `unidade_federativa` | Nome da UF. |
| `sigla_unidade_federativa` | Sigla da UF. |
| `regiao_do_brasil_id` | Região do Brasil. |

## Relacionamentos

- `unidade_federativa.regiao_do_brasil_id` -> `regiao_do_brasil`.
- `municipio.sigla_uf` -> `sigla_unidade_federativa`.

## Qualidade e observações

- Tabela de referência, estável.
