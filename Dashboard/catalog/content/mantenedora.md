---
table: MANTENEDORA
display_name: Mantenedoras (compradores)
description: Órgãos e entidades que compram medicamentos e insumos para o SUS (secretarias, fundos de saúde): uma linha por mantenedora. Origem: DATASUS (BPS). Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, compras
---

## O que é

Cadastro das mantenedoras, as entidades compradoras das compras públicas. A UF de uma compra é a UF do município da mantenedora. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Uma mantenedora (7.677 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `mantenedora_id` | Identificador da mantenedora (chave). |
| `cnpj_mantenedora` | CNPJ da mantenedora. |
| `nome_mantenedora` | Nome da mantenedora. |
| `municipio_id` | Município da mantenedora. |

## Relacionamentos

- `mantenedora.municipio_id` -> `municipio`.
- `mantenedora_compra_produto.mantenedora_id` e `instituicao.mantenedora_id` -> `mantenedora.mantenedora_id`.

## Qualidade e observações

- Uma mantenedora pode manter várias instituições (estabelecimentos de saúde).
