---
table: LEITOS
display_name: Leitos hospitalares (CNES)
description: Quantidade de leitos por instituição e competência mensal (gerais, SUS e UTI por tipo). Origem: DATASUS (CNES), jul/2007 a jan/2026. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, leitos
---

## O que é

Série mensal de leitos por estabelecimento de saúde, com leitos gerais, leitos SUS e leitos de UTI por tipo (adulto, pediátrico, neonatal, queimado e coronariana). Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Uma instituição em uma competência mensal (1,59 mi linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `leitos_id` | Identificador da linha (chave). |
| `data_de_competencia` | Mês de competência do CNES. |
| `quantidade_leitos_gerais` | Leitos gerais. |
| `quantidade_leitos_sus` | Leitos SUS. |
| `quantidade_leitos_uti / quantidade_leitos_uti_sus` | Leitos de UTI e de UTI SUS. |
| `quantidade_leitos_uti_adulto, _pediatrico, _neonatal, _queimado, _coronariana` | Leitos de UTI por tipo. |
| `quantidade_leitos_uti_sus_adulto, _pediatrico, _neonatal, _queimado, _coronariana` | Leitos de UTI SUS por tipo. |
| `instituicao_id` | Chave para `instituicao`. |

## Relacionamentos

- `instituicao_id` -> `instituicao`; pelo endereço da instituição chega-se a município, UF e região (view `v_endereco_completo`).

## Qualidade e observações

- Para o retrato atual, use o último snapshot (competência) de cada instituição; somar competências diferentes duplica leitos.
- Em jan/2026 o Brasil tinha 521.602 leitos gerais, 352.372 SUS e 64.089 de UTI (segundo esta base).
