---
table: ENDERECO
display_name: Endereços
description: Endereços de instituições de saúde: logradouro, CEP e coordenadas, ligados ao município. Origem: DATASUS (CNES). Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, territorio
---

## O que é

Cadastro de endereços usado por instituições de saúde, com coordenadas geográficas quando disponíveis. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Um endereço (446.107 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `endereco_id` | Identificador do endereço (chave). |
| `cep` | CEP. |
| `logradouro, numero_do_logradouro, complemento, bairro` | Endereço. |
| `latitude, longitude` | Coordenadas. |
| `municipio_id` | Chave para `municipio`. |

## Relacionamentos

- `endereco.municipio_id` -> `municipio`.
- `instituicao.endereco_id` -> `endereco.endereco_id`.
- A view `v_endereco_completo` já traz o endereço com município, UF e regiões.

## Qualidade e observações

- Contém dados de localização de estabelecimentos.
