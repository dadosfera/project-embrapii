# Documentação Técnica e Semântica - Schema DataSUS

## Visão Geral do Banco
Este banco integra dados de Hospitais e Leitos, BPS (Preços), BNAFAR (Estoque) e CNES.
- **Nota sobre Nulos:** Devido à integração de bases distintas, tabelas originadas apenas do BNAFAR ou Hospitais e Leitos podem ter dados nulos para campos presentes apenas no CNES.
- **Unidade de Medida:** Crucial para cálculos de preço e estoque (ML, DOSES, UN, KG, etc).

---

## 1. Geografia e Endereçamento

### Tabela: `regiao_do_brasil`
- `codigo_da_regiao_do_brasil`: 1-Norte, 2-Nordeste, 3-Sudeste, 4-Sul, 5-Centro-Oeste.

### Tabela: `unidade_federativa`
- Mapeia estados (sigla e nome) e vincula à região via `regiao_do_brasil_id`.

### Tabela: `municipio`
- `codigo_do_municipio`: Código IBGE de 7 dígitos.
- `populacao`: Dados do Censo 2022.
- **Relacionamento**: Conecta-se à `regiao_de_saude` para análises regionais de gestão.

### Tabela: `endereco`
- Contém `latitude` e `longitude` para mapas e `municipio_id` para JOINS geográficos.

---

## 2. Cadastro de Entidades (Hospitais, Fornecedores e Fabricantes)

### Tabela: `instituicao`
- `codigo_cnes`: Identificador único nacional de 7 dígitos.
- `codigo_tipo_unidade`: Define o perfil (05-Hospital Geral, 07-Especializado, 20-Pronto Socorro).
- `codigo_natureza_juridica`: 
    - 1000-1999: Hospital Público.
    - 2000-2999: Hospital Privado.
    - 3000-3999: Hospital Filantrópico.
- `codigo_esfera_administrativa`: M-Municipal, E-Estadual, F-Federal, D-Dupla.
- `codigo_turno_atendimento`: 06 indica atendimento 24h/dia.
- `origem_registro`: 'HOSPITAIS' ou 'BNAFAR'.

### Tabela: `mantenedora`
- Entidade administrativa que realiza compras para as instituições.
- **Regra**: Se CNPJ da mantenedora for igual ao da instituição, ela é autogestionada.

---

## 3. Catálogo de Produtos

### Tabela: `catmat`
- `codigo_catmat`: Código oficial de compras públicas.
- `descricao_catmat`: Nome técnico padronizado do medicamento ou insumo.

### Tabela: `produto`
- Vincula o `catmat_id` ao número de registro da `anvisa`.
- `generico`: Indica 'SIM', 'NÃO' ou 'N/A'.
- **Nota**: O BNAFAR não distingue genéricos pelo estoque, apenas pelo CATMAT.

---

## 4. Movimentação, Compras e Estoque

### Tabela: `mantenedora_compra_produto` (Fato de Compras)
- **Cálculos**: `preco_total` é o valor da transação; `preco_unitario` é o valor por item.
- `modalidade_de_compra`: PREGÃO, DISPENSA DE LICITAÇÃO, etc.
- `unidade_de_fornecimento`: Forma física (FRASCO, AMPOLA, COMPRIMIDO).
- `capacidade_da_unidade_de_fornecimento`: Volume ou quantidade por embalagem.

### Tabela: `instituicao_estoca_produto` (Fato de Estoque)
- `quantidade_do_item_em_estoque`: Saldo atual na data de posição.
- `tipo_do_produto`: 
    - B: Componente Básico.
    - E: Especializado.
    - S: Estratégico.
- `sigla_do_programa_de_saude`: Filtro para programas específicos (Ex: 'HIPERTEN' para Hipertensão, 'DIA' para Diabetes, 'COVID-19').

### Tabela: `leitos`
- `quantidade_leitos_sus`: Capacidade disponível para o sistema público.
- `quantidade_leitos_uti`: Total de leitos de terapia intensiva. Subdivididos em `adulto`, `pediatrico`, `neonatal`, `queimado` e `coronariana`.

---

## 5. Chaves de Ligação (Joins Comuns)
- **Para analisar estoque por cidade**: `instituicao_estoca_produto` -> `instituicao` -> `endereco` -> `municipio`.
- **Para analisar compras por fabricante**: `mantenedora_compra_produto` -> `fabricante`.
- **Para ver leitos por região**: `leitos` -> `instituicao` -> `endereco` -> `municipio` -> `regiao_de_saude` -> `macrorregiao_de_saude`.
- **Para filtrar medicamentos**: `instituicao_estoca_produto` -> `produto` -> `catmat`.