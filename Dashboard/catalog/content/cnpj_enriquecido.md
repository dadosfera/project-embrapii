---
table: CNPJ_ENRIQUECIDO
display_name: CNPJs enriquecidos (fornecedores e fabricantes)
description: Dados cadastrais complementares por CNPJ (razão social, natureza jurídica, país, situação cadastral e sócios no exterior), usados para análises de fornecedores e fabricantes. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, fornecedores
---

## O que é

Tabela de enriquecimento: para cada CNPJ consultado, traz razão social, natureza jurídica, país, situação cadastral e a indicação de sócio pessoa jurídica no exterior. Foi produzida pelo projeto a partir de consultas públicas de CNPJ. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Um CNPJ consultado (5.110 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `cnpj` | CNPJ consultado (chave). |
| `razao_social` | Razão social. |
| `codigo_natureza_juridica / descricao_natureza_juridica` | Natureza jurídica (código e descrição). |
| `codigo_pais / nome_pais` | País do cadastro. |
| `nacional_estrangeiro` | Indica se a empresa é nacional ou estrangeira. |
| `situacao_cadastral` | Situação cadastral do CNPJ. |
| `consultado_em` | Momento da consulta. |
| `erro_consulta` | Mensagem de erro, quando a consulta falhou. |
| `possui_socio_pj_exterior / nome_socio_pj_exterior` | Indica sócio pessoa jurídica no exterior e o nome dele. |
| `socios_consultado_em / socios_erro_consulta` | Momento e erro da consulta de sócios. |

## Relacionamentos

- `cnpj` corresponde a `fornecedor.cnpj_fornecedor` e `fabricante.cnpj_fabricante`.

## Qualidade e observações

- Dados de consulta pontual: refletem a situação no momento em `consultado_em`.
- Quando `erro_consulta` está preenchido, a consulta do CNPJ falhou naquela tentativa.
