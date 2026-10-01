---
table: FORNECEDOR
display_name: Fornecedores
description: Empresas que venderam produtos nas compras públicas de saúde: uma linha por fornecedor (CNPJ e nome). Origem: DATASUS (BPS). Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, fornecedores
---

## O que é

Cadastro de fornecedores das compras públicas de medicamentos e insumos. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Um fornecedor (3.109 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `fornecedor_id` | Identificador do fornecedor (chave). |
| `cnpj_fornecedor` | CNPJ do fornecedor. |
| `nome_fornecedor` | Nome do fornecedor. |

## Relacionamentos

- `mantenedora_compra_produto.fornecedor_id` -> `fornecedor.fornecedor_id`.
- O CNPJ pode ser cruzado com `cnpj_enriquecido.cnpj` para dados cadastrais.

## Qualidade e observações

- Os rankings de fornecedores do Dashboard somam `preco_total` das compras; lembre dos valores atípicos descritos em `mantenedora_compra_produto`.
