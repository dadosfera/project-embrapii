---
table: V_ENDERECO_COMPLETO
display_name: Endereços com território completo
description: View que junta cada endereço ao município, UF, região do Brasil, região de saúde e macrorregião de saúde. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, territorio
---

## O que é

Visão pronta para análises geográficas: o endereço já vem com toda a hierarquia territorial (município, UF, região do Brasil, região e macrorregião de saúde). Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Um endereço (443.163 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `endereco_id, cep, logradouro, numero_do_logradouro, complemento, bairro, latitude, longitude` | Campos de `endereco`. |
| `municipio_id, codigo_do_municipio, municipio, sigla_uf, populacao` | Município (código IBGE, nome, UF e população). |
| `codigo_da_unidade_federativa, unidade_federativa, sigla_unidade_federativa` | Unidade federativa. |
| `codigo_da_regiao_do_brasil, regiao_do_brasil` | Região do Brasil. |
| `codigo_da_regiao_de_saude, regiao_de_saude` | Região de saúde. |
| `codigo_macrorregiao_de_saude, macrorregiao_de_saude` | Macrorregião de saúde. |

## Relacionamentos

- Derivada de `endereco`, `municipio`, `unidade_federativa`, `regiao_do_brasil`, `regiao_de_saude` e `macrorregiao_de_saude`.
- `instituicao.endereco_id` -> `v_endereco_completo.endereco_id`.

## Qualidade e observações

- Tem menos linhas (443.163) que `endereco` (446.107): nem todo endereço chega à view.
