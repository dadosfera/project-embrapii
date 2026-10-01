---
table: PRODUTO
display_name: Produtos (apresentações CATMAT/ANVISA)
description: Produtos comprados e estocados no SUS: uma linha por apresentação, ligada a um item CATMAT e ao registro ANVISA. Origem: DATASUS (BPS e BNAFAR). Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, catalogo-catmat
---

## O que é

Cadastro de produtos (apresentações) que aparecem nas compras e nos estoques. Cada produto pertence a um item do catálogo CATMAT. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Um produto (52.952 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `produto_id` | Identificador do produto (chave). |
| `anvisa` | Registro do produto na ANVISA. |
| `generico` | Indicação de medicamento genérico. |
| `codigo_catmat` | Código CATMAT do item. |
| `catmat_id` | Chave para `catmat`. |

## Relacionamentos

- `produto.catmat_id` -> `catmat.catmat_id`.
- `mantenedora_compra_produto.produto_id` e `instituicao_estoca_produto.produto_id` -> `produto.produto_id`.

## Qualidade e observações

- Um mesmo item CATMAT pode ter vários produtos; para análises por medicamento agregue por `catmat_id`.
