---
table: FABRICANTE
display_name: Fabricantes
description: Fabricantes dos produtos comprados pelo SUS: uma linha por fabricante (CNPJ e nome). Origem: DATASUS (BPS). Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, fornecedores
---

## O que é

Cadastro de fabricantes dos produtos nas compras públicas. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Um fabricante (2.732 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `fabricante_id` | Identificador do fabricante (chave). |
| `cnpj_fabricante` | CNPJ do fabricante. |
| `nome_fabricante` | Nome do fabricante. |

## Relacionamentos

- `mantenedora_compra_produto.fabricante_id` -> `fabricante.fabricante_id`.
- O CNPJ pode ser cruzado com `cnpj_enriquecido.cnpj`.

## Qualidade e observações

- Os rankings de fabricantes do Dashboard somam `preco_total` das compras.
