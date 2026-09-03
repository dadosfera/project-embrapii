
# Documentação Técnica e Semântica - Schema DataSUS

## LLM Guidelines
* **Sintaxe PostgreSQL:** Todas as colunas estão em *snake_case* minúsculo. É **obrigatório** o uso de aspas duplas nos nomes das colunas e tabelas ao gerar queries (ex: `"produto_id"`, `"codigo_tipo_unidade"`).
* **Conexão de Produtos:** A tabela central de movimentação é a `"produto"`, **NÃO** a `"catmat"`. Nunca ligue o estoque ou compras diretamente ao `"catmat_id"`.
* **Estado Atual vs. Histórico:**
  * Para dados de "hoje", "atual" ou saldo, **SEMPRE** use as Materialized Views (`"mv_estoque_mais_recente"`, `"mv_leitos_mais_recente"`).
  * Para análises históricas, use as tabelas base (`"instituicao_estoca_produto"`, `"leitos"`).
* **Uso de Views:** Utilize `"v_endereco_completo"` para qualquer filtro geográfico e `"v_produto_completo"` para nomes de medicamentos.

---

## 1. Geografia e Endereçamento

Para consultas que exigem filtros geográficos, priorize a View `"v_endereco_completo"`. Para referências diretas, considere os domínios abaixo:

* **`regiao_do_brasil`**: 
  * `codigo_da_regiao_do_brasil`: 1-Norte, 2-Nordeste, 3-Sudeste, 4-Sul, 5-Centro-Oeste.
* **`unidade_federativa`**: Mapeia estados (sigla e nome) e vincula à região.
* **`municipio`**: 
  * `codigo_do_municipio`: Código IBGE de 7 dígitos.
  * `populacao`: Dados do Censo 2022.
* **`endereco`**: Contém `latitude` e `longitude` para mapas geolocalizados.

---

## 2. Cadastro de Entidades (Hospitais, Gestores e Mercado)

### Tabela: `"instituicao"` (CNES)
Cadastro de unidades de saúde e infraestrutura.
* **`codigo_cnes`**: Identificador único nacional de 7 dígitos.
* **`codigo_tipo_unidade`**: Define o perfil clínico:
  * `05`: Hospital Geral
  * `07`: Especializado
  * `20`: Pronto Socorro
* **`codigo_natureza_juridica`**: Define o tipo de administração:
  * `1000-1999`: Hospital Público
  * `2000-2999`: Hospital Privado
  * `3000-3999`: Hospital Filantrópico
* **`codigo_esfera_administrativa`**: M - Municipal, E - Estadual, F - Federal, D - Dupla, S - SEM.
* **`codigo_turno_atendimento`**: `06` indica atendimento 24h/dia.
* **`origem_registro`**: Pode ser 'HOSPITAIS' ou 'BNAFAR'.

### Tabela: `"mantenedora"`
Entidade administrativa que realiza compras.
* **Regra de Negócio**: Se o CNPJ da mantenedora for igual ao da instituição, ela é considerada autogestionada.

---

## 3. Catálogo de Produtos

Priorize a view `"v_produto_completo"` para relacionar IDs a nomes reais.
* **`catmat`**: 
  * `codigo_catmat`: Código oficial de compras públicas.
  * `descricao_catmat`: Nome técnico padronizado do medicamento ou insumo.
* **`produto`**: Eixo de ligação obrigatório.
  * Vincula o `catmat_id` ao número de registro da `anvisa`.
  * `generico`: Indica 'SIM', 'NÃO' ou 'N/A'. *(Nota: O BNAFAR não distingue genéricos pelo estoque, apenas pelo CATMAT).*

---

## 4. Movimentação, Compras, Estoque e Leitos

### Tabela Fato (Compras): `"mantenedora_compra_produto"`
* **Cálculos e Valores**: `preco_total` é o valor total da transação; `preco_unitario` é o valor por item.
* **Modalidades**: `modalidade_de_compra` inclui 'PREGÃO', 'DISPENSA DE LICITAÇÃO', etc.
* **Acondicionamento**: `unidade_de_fornecimento` (FRASCO, AMPOLA, COMPRIMIDO) e `capacidade_da_unidade_de_fornecimento` (Volume/Quantidade).

### Tabela Fato (Estoque Histórico): `"instituicao_estoca_produto"`
* **Saldo**: `quantidade_do_item_em_estoque` representa o saldo atual na data de posição.
* **Classificação (`tipo_do_produto`)**: 
  * `B`: Componente Básico
  * `E`: Especializado
  * `S`: Estratégico
* **Filtro de Gestão (`sigla_do_programa_de_saude`)**: Usado para programas específicos (Ex: 'HIPERTEN' para Hipertensão, 'DIA' para Diabetes, 'COVID-19').

### Tabela Fato (Capacidade): `"leitos"`
* **`quantidade_leitos_sus`**: Capacidade disponível exclusivamente para o sistema público.
* **`quantidade_leitos_uti`**: Total de leitos de terapia intensiva. É subdividido detalhadamente em `adulto`, `pediatrico`, `neonatal`, `queimado` e `coronariana`.

---

## 5. Chaves de Ligação (Joins Comuns)

Em vez de construir trilhas imensas de tabelas, utilize as Views ou os padrões recomendados abaixo:

* **Para analisar Estoque Atual por Estado/Município:** `"mv_estoque_mais_recente"` -> `"instituicao"` -> `"v_endereco_completo"` *(ligando por `instituicao.endereco_id = v_endereco_completo.endereco_id`)*.
* **Para descobrir o Nome do Medicamento em Estoque/Compra:** `"mv_estoque_mais_recente"` (ou `"mantenedora_compra_produto"`) -> `"v_produto_completo"` *(ligando por `produto_id`)*.
* **Para analisar Compras por Fabricante:** `"mantenedora_compra_produto"` -> `"fabricante"` *(ligando por `fabricante_id`)*.
* **Para ver Leitos Atuais por Região de Saúde:** `"mv_leitos_mais_recente"` -> `"instituicao"` -> `"v_endereco_completo"`.