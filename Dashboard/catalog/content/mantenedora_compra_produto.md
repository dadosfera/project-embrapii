---
table: MANTENEDORA_COMPRA_PRODUTO
display_name: Compras de medicamentos (mantenedoras)
description: Compras públicas de medicamentos e insumos: uma linha por compra de um produto por uma mantenedora, com fornecedor, fabricante, quantidade e preço. Origem: DATASUS (BPS), 2020 a 2025. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, compras
---

## O que é

Registros de compras públicas de medicamentos e insumos de saúde (DATASUS / Banco de Preços em Saúde). Base das telas de Compras, Mapa e Fornecedores do Dashboard. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Uma compra de um produto por uma mantenedora (263.562 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `mantenedora_compra_produto_id` | Identificador da compra (chave). |
| `data_de_compra` | Data da compra. É anual: sempre 1º de janeiro, de 2020 a 2025. |
| `data_de_insercao` | Data de inserção do registro. |
| `modalidade_de_compra` | Modalidade da compra. |
| `tipo_da_compra` | ADMINISTRATIVA (rotina) ou JUDICIAL (compra por ordem judicial). |
| `capacidade / unidade_de_medida` | Capacidade e unidade de medida da apresentação. |
| `quantidade_de_itens` | Quantidade de itens comprados. |
| `preco_unitario` | Preço unitário (R$). |
| `preco_total` | Preço total da compra (R$). |
| `fornecedor_id, fabricante_id, produto_id, mantenedora_id` | Chaves para fornecedor, fabricante, produto e mantenedora. |

## Relacionamentos

- `fornecedor_id` -> `fornecedor`.
- `fabricante_id` -> `fabricante`.
- `produto_id` -> `produto` (e, por ele, `catmat`).
- `mantenedora_id` -> `mantenedora` (e, por ela, `municipio` e UF).

## Qualidade e observações

- `data_de_compra` não tem granularidade mensal: toda compra cai em 1º de janeiro do ano.
- Há valores fora de escala: por exemplo, um registro de seringa (CATMAT BR0439678) soma R$ 22,7 bi em 2025 (6 compras, mesmo fornecedor). Esses valores dominam totais de alguns anos; ao analisar tendências, compare também o número de compras.
- No conjunto total: 263.562 compras, R$ 50,9 bi, 2020 a 2025, 3.109 fornecedores e 760 mantenedoras com compra.
