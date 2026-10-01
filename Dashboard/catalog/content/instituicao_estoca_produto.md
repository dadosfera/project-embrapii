---
table: INSTITUICAO_ESTOCA_PRODUTO
display_name: Estoque de medicamentos por instituição
description: Posição de estoque de medicamentos: uma linha por instituição e produto (a posição mais recente). Origem: DATASUS (BNAFAR / Hórus), fev/2024 a fev/2026. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, estoque
---

## O que é

Posição de estoque de medicamentos e insumos nos estabelecimentos de saúde (BNAFAR). Nesta cópia fica apenas a posição mais recente de cada combinação instituição x produto. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

A posição mais recente de um produto em uma instituição (3,3 mi linhas, posições de fev/2024 a fev/2026).

## Colunas principais

| Coluna | Significado |
|---|---|
| `instituicao_estoca_produto_id` | Identificador da posição (chave). |
| `data_de_posicao_no_estoque` | Data da posição de estoque. |
| `quantidade_do_item_em_estoque` | Quantidade em estoque. |
| `numero_do_lote` | Lote. |
| `data_de_validade` | Validade do lote. |
| `tipo_do_produto` | B = Básico, E = Especializado, S = Estratégico, O = recursos próprios do ente. |
| `sigla_do_programa_de_saude / descricao_do_programa_de_saude` | Programa de saúde vinculado. |
| `sigla_do_sistema_de_origem` | Sistema de origem do dado (por exemplo Hórus). |
| `instituicao_id, produto_id` | Chaves para instituição e produto. |

## Relacionamentos

- `instituicao_id` -> `instituicao`.
- `produto_id` -> `produto` (e, por ele, `catmat`).

## Qualidade e observações

- Recorte: a tabela de origem tem cerca de 248 mi de linhas; aqui está só a posição mais recente por instituição x produto, então não serve para séries históricas de estoque.
- As quantidades têm unidades inconsistentes entre registros (algumas UFs somam centenas de bilhões de unidades); para comparar UFs, prefira contagens de instituições, de medicamentos e de posições zeradas.
- Os tipos do produto seguem a classificação por componente da Assistência Farmacêutica (RENAME): Básico, Especializado, Estratégico e recursos próprios.
