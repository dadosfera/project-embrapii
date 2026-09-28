# Dashboard EMBRAPII / DATASUS — dicionário da knowledge base

Dados públicos do SUS (compras de medicamentos e insumos, estoque de medicamentos nas unidades de saúde e leitos do CNES),
organizados pelo projeto UFMG/EMBRAPII e publicados no data app "Dashboard" do Módulo de Inteligência da Dadosfera.
Fonte: Snowflake `DADOSFERA_PRD_DADOSFERADEMO.EMBRAPII_DATASUS` (cópia do Postgres `datalake_db2` da UFMG).
Os arquivos desta base são **agregados**; o detalhe de um medicamento específico chega pelo contexto da tela (ui_context).

## Telas do app
- **Medicamentos**: busca no catálogo CATMAT, seleciona um item e mostra KPIs (estoque total, instituições com registro,
  instituições com estoque zerado, preço médio de compra), lotes vencendo em 90 dias, estoque por UF, evolução do preço,
  top fornecedores, top fabricantes e o histórico de compras.
- **Compras**: KPIs e rankings de compras públicas por período, tipo (ADMINISTRATIVA / JUDICIAL) e modalidade.
- **Leitos**: leitos gerais, SUS e UTI por UF e por tipo de UTI, evolução mensal.
- **Mapa / Fornecedores**: distribuição geográfica das compras e ranking de fornecedores por UF.

## Conceitos
- **CATMAT**: catálogo de materiais do governo federal; cada `catmat_id` pode ter vários `produto_id` (apresentações/registros ANVISA).
- **Mantenedora**: órgão/entidade que compra (secretarias, fundos de saúde). UF da compra = UF do município da mantenedora.
- **Tipo da compra**: ADMINISTRATIVA (rotina) ou JUDICIAL (compra por ordem judicial).
- **Estoque atual**: posição mais recente por instituição × medicamento (recorte de 3,3 mi posições de fev/2024 a fev/2026).
- **Leitos atuais**: último snapshot (competência) de cada instituição no CNES.

## Arquivos
| arquivo | grão | colunas |
|---|---|---|
| compras_por_ano.csv | ano × tipo da compra | valor_total (R$), numero_compras, quantidade_itens |
| compras_por_uf_ano.csv | UF da mantenedora × ano | valor_total, numero_compras, numero_mantenedoras |
| compras_por_modalidade.csv | modalidade × tipo | valor_total, numero_compras |
| medicamentos_top_compras.csv | CATMAT (400 maiores em valor) | valor_total, numero_compras, quantidade_itens, preco_unitario_medio/min/max, numero_fornecedores, numero_mantenedoras, primeira_compra, ultima_compra |
| medicamentos_preco_por_ano.csv | CATMAT (100 maiores) × ano | preco_unitario_medio, valor_total, numero_compras |
| fornecedores_top.csv | fornecedor (300 maiores) | cnpj, valor_total, numero_compras, numero_medicamentos, numero_mantenedoras |
| fabricantes_top.csv | fabricante (300 maiores) | cnpj, valor_total, numero_compras, numero_medicamentos |
| estoque_por_uf.csv | UF da instituição | estoque_total (unidades), numero_instituicoes, numero_medicamentos, posicoes_zeradas, posicoes |
| medicamentos_top_estoque.csv | CATMAT (400 com mais instituições) | estoque_total, instituicoes_com_registro, instituicoes_estoque_zerado, posicoes_vencendo_90d |
| leitos_por_uf.csv | UF | leitos_gerais, leitos_sus, leitos_uti, leitos_uti_sus, uti_adulto/pediatrico/neonatal/coronariana/queimado, numero_instituicoes, populacao_uf |
| leitos_evolucao_mensal.csv | competência (mês) | leitos_gerais, leitos_sus, leitos_uti, leitos_uti_sus, numero_instituicoes (Brasil) |

## Totais
- Compras: 263.562 registros, R$ 50,9 bi, 2020 a 2025, 3.109 fornecedores, 760 mantenedoras.
- Catálogo: 21.832 itens CATMAT, 52.952 produtos, 603.572 instituições cadastradas.
- Leitos: competências de jul/2007 a jan/2026; em jan/2026 o Brasil tinha 521.602 leitos gerais, 352.372 SUS e 64.089 de UTI.

## Qualidade dos dados (avise o usuário quando pesar na resposta)
- `data_de_compra` é **anual** (sempre 1º de janeiro): não há granularidade mensal de compras.
- Há registros de compra com preço/quantidade fora da escala (ex.: seringa CATMAT BR0439678 com R$ 22,7 bi em 6 compras,
  fornecedor MEDICAL MERCANTIL). Esses outliers dominam os totais de 2021 e 2025; ao analisar tendência, mencione isso
  e, quando fizer sentido, compare também número de compras.
- `estoque_total` tem quantidades lançadas em unidades inconsistentes (SE e ES somam centenas de bilhões de unidades);
  para comparar UFs prefira `numero_instituicoes`, `numero_medicamentos` e `posicoes_zeradas`.
