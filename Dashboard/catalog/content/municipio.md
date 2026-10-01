---
table: MUNICIPIO
display_name: Municípios
description: Municípios brasileiros (IBGE): código, nome, UF, população e região de saúde. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, territorio
---

## O que é

Cadastro dos 5.570 municípios do Brasil, com população e a região de saúde a que pertencem. Fonte: IBGE / DATASUS. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Um município (5.570 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `codigo_do_municipio` | Código do município (IBGE). |
| `municipio` | Nome do município. |
| `sigla_uf` | Sigla da UF. |
| `populacao` | População. |
| `regiao_de_saude_id` | Região de saúde do município. |

## Relacionamentos

- `municipio.regiao_de_saude_id` -> `regiao_de_saude`.
- `municipio.sigla_uf` -> `unidade_federativa.sigla_unidade_federativa`.
- `endereco.municipio_id` e `mantenedora.municipio_id` apontam para o município.

## Qualidade e observações

- A população é um valor único por município (não é série histórica).
