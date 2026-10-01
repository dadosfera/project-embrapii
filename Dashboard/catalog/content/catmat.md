---
table: CATMAT
display_name: Catálogo CATMAT
description: Catálogo de materiais do governo federal (CATMAT): uma linha por item. Base de referência para identificar medicamentos e insumos em compras e estoque. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, catalogo-catmat
---

## O que é

Lista de itens do CATMAT, o catálogo de materiais do governo federal usado para identificar medicamentos e insumos de saúde nas compras públicas e nas posições de estoque do SUS (DATASUS). Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Um item CATMAT (21.832 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `catmat_id` | Identificador interno do item (chave). |
| `codigo_catmat` | Código do item no CATMAT, por exemplo BR0439678. |
| `descricao_catmat` | Descrição do item. |

## Relacionamentos

- `produto.catmat_id` aponta para esta tabela: um item CATMAT pode ter vários produtos (apresentações / registros ANVISA).

## Qualidade e observações

- Códigos com prefixo BRB, BRE, BRS ou BRO são componentes da Assistência Farmacêutica no BNAFAR: Básico, Especializado, Estratégico e recursos próprios do ente, respectivamente.
- Sufixos no estilo U0042 indicam unidades de fornecimento (apresentação do item).
- Os códigos também aparecem em `produto.codigo_catmat`.
