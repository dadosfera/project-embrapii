# 📘 Documentação do Modelo de Dados

Este documento descreve a organização das tabelas do schema `public`, com foco na estrutura das colunas e no significado dos dados armazenados.

---

## 🗺️ Tabela: Endereco

Armazena informações de localização geográfica e endereços no território brasileiro.

### 📋 Colunas

| Coluna                        | Descrição                                                                 |
|-------------------------------|---------------------------------------------------------------------------|
| Endereco_ID                   | Identificador único do endereço.                                          |
| Regiao_do_Brasil              | Região geográfica do Brasil (Norte, Nordeste, Centro-Oeste, Sudeste, Sul).|
| Unidade_Federativa            | Sigla da Unidade Federativa (ex: PA, SP, RJ).                             |
| Codigo_do_IBGE                | Código do município segundo o IBGE.                                       |
| Municipio                     | Nome do município.                                                        |
| Bairro                        | Nome do bairro.                                                           |
| Logradouro                    | Nome do logradouro (rua, avenida, travessa, etc.).                        |
| Numero_do_Logradouro          | Número do imóvel no logradouro.                                           |
| Complemento                   | Complemento do endereço (ex: apto, bloco, sala).                          |
| CEP                           | Código de Endereçamento Postal.                                           |
| Latitude                      | Coordenada de latitude do endereço.                                       |
| Longitude                     | Coordenada de longitude do endereço.                                      |

---

## 🏭 Tabela: Fabricante

Armazena informações sobre os fabricantes de produtos, principalmente do setor farmacêutico ou hospitalar.

### 📋 Colunas

| Coluna            | Descrição                                                                 |
|-------------------|---------------------------------------------------------------------------|
| Fabricante_ID     | Identificador único do fabricante.                                        |
| CNPJ_Fabricante   | Cadastro Nacional da Pessoa Jurídica (CNPJ) do fabricante.                |
| Nome_Fabricante   | Razão social ou nome do fabricante.                                       |


---

## 🚚 Tabela: Fornecedor

Armazena informações sobre os fornecedores de produtos, que podem atuar na distribuição ou comercialização.

### 📋 Colunas

| Coluna            | Descrição                                                                 |
|-------------------|---------------------------------------------------------------------------|
| Fornecedor_ID     | Identificador único do fornecedor.                                        |
| CNPJ_Fornecedor   | Cadastro Nacional da Pessoa Jurídica (CNPJ) do fornecedor.                |
| Nome_Fornecedor   | Razão social ou nome do fornecedor.                                       |


---

## 🏥 Tabela: Instituicao

Armazena informações cadastrais e administrativas das instituições de saúde, como hospitais, clínicas e maternidades.

### 📋 Colunas

| Coluna                           | Descrição                                                                 |
|----------------------------------|---------------------------------------------------------------------------|
| Instituicao_ID                   | Identificador único da instituição.                                       |
| Codigo_CNES                      | Código Nacional de Estabelecimentos de Saúde (CNES).                      |
| Nome_Instituicao                 | Nome fantasia da instituição.                                             |
| Razao_Social                     | Razão social da instituição.                                              |
| Email                            | Endereço de e-mail da instituição.                                        |
| Telefone                         | Telefone de contato da instituição.                                       |
| Endereco_ID                      | Identificador do endereço associado à instituição.                        |
| Tipo_de_Gestao                   | Tipo de gestão da instituição (ex: municipal, estadual, privada).         |
| Codigo_do_Tipo_da_Unidade        | Código do tipo da unidade de saúde.                                       |
| Descricao_do_Tipo_da_Unidade     | Descrição do tipo da unidade (ex: hospital geral).                        |
| Codigo_da_Natureza_Juridica      | Código da natureza jurídica da instituição.                               |
| Descricao_da_Natureza_Juridica   | Descrição da natureza jurídica (ex: hospital privado).                    |
| Motivo_da_Desabilitacao          | Motivo de desabilitação da instituição, quando aplicável.                 |
| CNPJ_Instituicao                 | CNPJ da instituição.                                                      |

---

## 🛒 Tabela: Instituicao_Compra_Produto

Registra as compras de produtos realizadas pelas instituições, incluindo informações financeiras, quantitativas e de relacionamento com fornecedores, fabricantes e produtos.

### 📋 Colunas

| Coluna                                      | Descrição                                                                |
|---------------------------------------------|--------------------------------------------------------------------------|
| Instituicao_Compra_Produto_ID               | Identificador único do registro de compra.                               |
| Data_de_Compra                              | Data em que a compra foi realizada.                                      |
| Data_de_Insercao                            | Data em que o registro foi inserido no sistema.                          |
| Modalidade_de_Compra                        | Modalidade da compra (ex: Pregão, Dispensa, Inexigibilidade).            |
| Tipo_da_Compra                              | Tipo da compra (ex: administrativa).                                     |
| Quantidade_de_Itens                         | Quantidade total de itens adquiridos.                                    |
| Preco_Unitario                              | Preço unitário do item comprado.                                         |
| Preco_Total                                 | Valor total da compra.                                                   |
| Unidade_de_Medida                           | Unidade de medida do produto (ex: mg, ml, unidade).                      |
| Capacidade                                  | Capacidade ou dosagem do produto.                                        |
| Unidade_de_Fornecimento                     | Forma de fornecimento do produto (ex: comprimido, frasco).               |
| Capacidade_da_Unidade_de_Fornecimento       | Capacidade associada à unidade de fornecimento.                          |
| Instituicao_ID                              | Identificador da instituição compradora.                                 |
| Fornecedor_ID                               | Identificador do fornecedor.                                             |
| Fabricante_ID                               | Identificador do fabricante.                                             |
| Produto_ID                                  | Identificador do produto adquirido.                                      |

---

## 📦 Tabela: Instituicao_Estoca_Produto

Registra a posição de estoque dos produtos nas instituições, incluindo quantidade disponível, lote, validade e informações de origem do sistema.

### 📋 Colunas

| Coluna                           | Descrição                                                                 |
|----------------------------------|---------------------------------------------------------------------------|
| Instituicao_Estoca_Produto_ID    | Identificador único do registro de estoque.                               |
| Data_de_Posicao_no_Estoque       | Data de referência da posição do estoque.                                 |
| Quantidade_do_Item_em_Estoque    | Quantidade disponível do produto em estoque na data informada.            |
| Numero_do_Lote                   | Número do lote do produto.                                                |
| Data_de_Validade                 | Data de validade do produto.                                              |
| Tipo_do_Produto                  | Classificação do produto (ex: B, E, S, O.).                               |
| Sigla_do_Programa_de_Saude       | Sigla do programa de saúde associado ao produto.                          |
| Descricao_do_Programa_de_Saude   | Descrição do programa de saúde.                                           |
| Sigla_do_Sistema_de_Origem       | Sistema de origem da informação de estoque.                               |
| Instituicao_ID                   | Identificador da instituição responsável pelo estoque.                    |
| Produto_ID                       | Identificador do produto em estoque.                                      |

---

## 🛏️ Tabela: Leitos

Armazena informações sobre a capacidade de leitos das instituições de saúde, incluindo leitos gerais e diferentes classificações de UTI, com separação entre SUS e não SUS.

### 📋 Colunas

| Coluna                                      | Descrição                                                                 |
|---------------------------------------------|---------------------------------------------------------------------------|
| Leitos_ID                                   | Data de referência das informações de leitos.                             |
| Data_de_Competencia                         | Data de referência das informações de leitos.                             |
| Quantidade_Leitos_Gerais                    | Quantidade total de leitos gerais da instituição.                         |
| Quantidade_Leitos_SUS                       | Quantidade de leitos gerais destinados ao SUS.                            |
| Quantidade_Leitos_UTI                       | Quantidade total de leitos de UTI.                                        |
| Quantidade_Leitos_UTI_SUS                   | Quantidade de leitos de UTI destinados ao SUS.                            |
| Quantidade_Leitos_UTI_Adulto                | Quantidade de leitos de UTI adulto.                                       |
| Quantidade_Leitos_UTI_SUS_Adulto            | Quantidade de leitos de UTI adulto destinados ao SUS.                     |
| Quantidade_Leitos_UTI_Pediatrico            | Quantidade de leitos de UTI pediátrico.                                   |
| Quantidade_Leitos_UTI_SUS_Pediatrico        | Quantidade de leitos de UTI pediátrico destinados ao SUS.                 |
| Quantidade_Leitos_UTI_Neonatal              | Quantidade de leitos de UTI neonatal.                                     |
| Quantidade_Leitos_UTI_SUS_Neonatal          | Quantidade de leitos de UTI neonatal destinados ao SUS.                   |
| Quantidade_Leitos_UTI_Queimado              | Quantidade de leitos de UTI para queimados.                               |
| Quantidade_Leitos_UTI_SUS_Queimado          | Quantidade de leitos de UTI para queimados destinados ao SUS.             |
| Quantidade_Leitos_UTI_Coronariana           | Quantidade de leitos de UTI coronariana.                                  |
| Quantidade_Leitos_UTI_SUS_Coronariana       | Quantidade de leitos de UTI coronariana destinados ao SUS.                |
| Instituicao_ID                              | Identificador da instituição à qual os leitos pertencem.                  |

---
## 📦 Tabela: Produto

Armazena o cadastro de produtos, com base na classificação CATMAT, incluindo informações regulatórias e identificação de produtos genéricos.

### 📋 Colunas

| Coluna            | Descrição                                                                |
|-------------------|--------------------------------------------------------------------------|
| Produto_ID        | Identificador único do produto.                                          |
| Codigo_CATMAT     | Código CATMAT (Catálogo de Materiais) utilizado em compras públicas.     |
| Descricao_CATMAT  | Descrição padronizada do produto conforme o CATMAT.                      |
| Anvisa            | Número de registro do produto na ANVISA, quando aplicável.               |
| Generico          | Indica se o produto é genérico (S / N).                                  |

---