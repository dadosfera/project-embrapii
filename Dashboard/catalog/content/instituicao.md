---
table: INSTITUICAO
display_name: Instituições de saúde (CNES)
description: Estabelecimentos de saúde cadastrados no CNES: uma linha por instituição, com tipo, natureza jurídica, esfera administrativa, turnos e serviços. Origem: DATASUS (CNES). Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, estoque
---

## O que é

Cadastro de estabelecimentos de saúde (CNES) que registram estoque de medicamentos e leitos. Faz parte do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicado na plataforma Dadosfera.

## Grão (uma linha =)

Uma instituição (603.572 linhas).

## Colunas principais

| Coluna | Significado |
|---|---|
| `instituicao_id` | Identificador da instituição (chave). |
| `codigo_cnes` | Código no CNES. |
| `codigo_unidade` | Código da unidade. |
| `cnpj_instituicao, nome_instituicao, razao_social` | CNPJ, nome e razão social. |
| `tipo_de_gestao` | Tipo de gestão. |
| `codigo_tipo_unidade / descricao_tipo_unidade` | Tipo de unidade de saúde. |
| `codigo_da_natureza_juridica / descricao_da_natureza_juridica` | Natureza jurídica. |
| `codigo_natureza_organizacao / descricao_natureza_organizacao` | Natureza da organização. |
| `codigo_nivel_hierarquia / descricao_nivel_hierarquia` | Nível de hierarquia. |
| `codigo_esfera_administrativa / descricao_esfera_administrativa` | Esfera administrativa. |
| `codigo_turno_atendimento / descricao_turno_atendimento` | Turno de atendimento. |
| `tem_centro_cirurgico, tem_centro_obstetrico, tem_centro_neonatal` | Indicadores de centros disponíveis. |
| `atendimento_hospitalar, atendimento_ambulatorial, atendimento_sus, tem_servico_apoio` | Indicadores de tipos de atendimento. |
| `motivo_da_desabilitacao` | Motivo de desabilitação, quando houver. |
| `telefone, email` | Contato. |
| `origem_registro` | Origem do registro. |
| `mantenedora_id, endereco_id` | Chaves para mantenedora e endereço. |

## Relacionamentos

- `instituicao.mantenedora_id` -> `mantenedora`.
- `instituicao.endereco_id` -> `endereco`.
- `instituicao_estoca_produto.instituicao_id` e `leitos.instituicao_id` -> `instituicao.instituicao_id`.

## Qualidade e observações

- Contém dados de contato (telefone, e-mail) de estabelecimentos; trate com o cuidado devido.
