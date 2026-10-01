---
key: dataapp
display_name: Dashboard EMBRAPII · DATASUS
description: Data app com visão pública do SUS: medicamentos (busca no catálogo CATMAT, preços e estoque), compras públicas, leitos hospitalares e fornecedores. Dados públicos do DATASUS organizados pelo projeto UFMG/EMBRAPII e publicados na plataforma Dadosfera.
tags: embrapii, datasus, saude-publica, dataapp
location: intelligence
---

## O que é

Aplicação web do projeto Dashboard EMBRAPII / DATASUS (UFMG/EMBRAPII), publicada no Módulo de Inteligência da plataforma Dadosfera. Reúne dados públicos do SUS sobre medicamentos e insumos, compras, estoque, leitos e fornecedores, com um assistente para perguntas sobre os dados da tela.

- **Abrir o data app:** {{url}}
- **Sobre o projeto:** [UFMG e startup mineira vão criar IA para responder a perguntas sobre o SUS](https://www.ufmg.br/comunicacao/assessoria-de-imprensa/releases/pesquisa-e-inovacao/ufmg-e-startup-mineira-vao-criar-ia-para-responder-a-perguntas-sobre-o-sus/)

## Páginas

| Página | O que mostra |
|---|---|
| Início | Visão geral dos indicadores. |
| Medicamentos | Busca no catálogo CATMAT (itens agrupados), com KPIs de estoque, instituições com registro e estoque zerado, preço médio de compra, lotes vencendo em 90 dias, estoque por UF, evolução do preço, top fornecedores e fabricantes e histórico de compras. |
| Compras | KPIs e rankings de compras públicas com filtros por ano, medicamento, fornecedor e estado, e alerta de valores atípicos (outliers). |
| Leitos | Leitos gerais, SUS e UTI por UF e por tipo de UTI, com evolução mensal. |
| Mapa | Distribuição geográfica das compras. |
| Fornecedores | Ranking de fornecedores por UF. |

## De onde vêm os dados

Os dados vêm de 17 tabelas do Catálogo, todas documentadas:

- [Compras de medicamentos (mantenedoras)]({{asset:MANTENEDORA_COMPRA_PRODUTO}})
- [Catálogo CATMAT]({{asset:CATMAT}})
- [Produtos (apresentações CATMAT/ANVISA)]({{asset:PRODUTO}})
- [Estoque de medicamentos por instituição]({{asset:INSTITUICAO_ESTOCA_PRODUTO}})
- [Leitos hospitalares (CNES)]({{asset:LEITOS}})
- [Instituições de saúde (CNES)]({{asset:INSTITUICAO}})
- [Fornecedores]({{asset:FORNECEDOR}})
- [Fabricantes]({{asset:FABRICANTE}})
- [CNPJs enriquecidos (fornecedores e fabricantes)]({{asset:CNPJ_ENRIQUECIDO}})
- [Mantenedoras (compradores)]({{asset:MANTENEDORA}})
- [Endereços]({{asset:ENDERECO}})
- [Endereços com território completo]({{asset:V_ENDERECO_COMPLETO}})
- [Municípios]({{asset:MUNICIPIO}})
- [Regiões de saúde]({{asset:REGIAO_DE_SAUDE}})
- [Macrorregiões de saúde]({{asset:MACRORREGIAO_DE_SAUDE}})
- [Unidades federativas]({{asset:UNIDADE_FEDERATIVA}})
- [Regiões do Brasil]({{asset:REGIAO_DO_BRASIL}})

## Qualidade e observações

- A data de compra é anual (sempre 1º de janeiro): não há granularidade mensal de compras.
- Há registros de compra com valores fora de escala (por exemplo, uma seringa com R$ 22,7 bi em 2025); o app sinaliza esses casos.
- O estoque é a posição mais recente por instituição e produto (fev/2024 a fev/2026).
