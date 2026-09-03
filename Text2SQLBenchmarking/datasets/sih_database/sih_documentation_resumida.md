# Dicionário de Dados e Guia de Contexto SQL - SIH-RS

Este documento descreve o esquema de banco de dados PostgreSQL para o Sistema de Informações Hospitalares (SIH-RS). 

---

## 🚀 Regras Críticas de Sintaxe PostgreSQL
* **Identificadores:** Todos os nomes de colunas **DEVEM** usar aspas duplas. Ex: `"SEXO"`, `"IDADE"`, `"VAL_TOT"`.
* **Mapeamento de Sexo:** 
    * `1` = Masculino
    * `3` = Feminino
    * *Nota:* Nunca utilize o valor `2`.
* **Filtros Geográficos:** Sempre realize `JOIN` entre `internacoes` e `municipios` para filtragens por nome de cidade ou estado.

---

## 📊 Tabelas Principais (Fatos)

### 1. `internacoes` (Tabela Mestra)
Registro principal de internações hospitalares (AIH).
* **Finalidade:** Estatísticas de internação, custos, tempo de permanência e demografia.
* **Colunas Chave:** * `"N_AIH"`: Chave primária.
    * `"CNES"`: Código do hospital.
    * `"DIAG_PRINC"`: CID-10 principal.
    * `"VAL_TOT"`: Valor total da internação.
    * `"QT_DIARIAS"`: Quantidade de diárias (use para cálculo de permanência em UTI).
* **Nota:** Não use para contagem de mortes ou procedimentos específicos (veja tabelas próprias abaixo).

### 2. `mortes` (Estatísticas de Óbitos)
Tabela primária para qualquer consulta sobre mortalidade ou óbitos.
* **Uso:** "Quantas mortes...", "Taxa de mortalidade...".
* **Relacionamento:** `JOIN internacoes ON mortes."N_AIH" = internacoes."N_AIH"`.

### 3. `procedimentos` (Estatísticas de Procedimentos)
Tabela primária para contagem de intervenções médicas.
* **Colunas Chave:** `"PROC_REA"` (Código), `"NOME_PROC"` (Descrição).
* **Nota:** Diferente de CID-10; refere-se ao que foi feito, não à doença.

---

## 📚 Tabelas de Referência (Lookup)

### 4. `cid10` (Descrições de Doenças)
**APENAS PARA LOOKUP.** Nunca use para contar doenças.
* **Uso:** `JOIN internacoes ON internacoes."DIAG_PRINC" = cid10."CID"`.
* **Filtro:** Use para localizar grupos clínicos (ex: 'cardiovascular') e filtrar as tabelas de fatos.

### 5. `municipios` e `dado_ibge`
* `municipios`: Localização geográfica (lat/long) e nomes de cidades.
* `dado_ibge`: Dados socioeconômicos, população e IDEB dos municípios.

### 6. `hospital`
Informações sobre os estabelecimentos de saúde.
* `"NATUREZA"`: `00` (Público), `50` (Privado), `60/61` (Filantrópico).

---

## 🔍 Tabelas de Detalhes Específicos

| Tabela | Uso Principal | Coluna Importante |
| :--- | :--- | :--- |
| `uti_detalhes` | Custos e marcadores de UTI | `"VAL_UTI"`, `"MARCA_UTI"` |
| `obstetricos` | Gravidez, parto e pré-natal | `"INSC_PN"` (se não nulo, indica pré-natal) |
| `condicoes_especificas` | Testes positivos (ex: VDRL) | `"IND_VDRL"` |
| `instrucao` | Escolaridade do paciente | `"INSTRU"` (01-06) |
| `vincprev` | Vínculo previdenciário | `"VINCPREV"` (1=Empregado, 5=Aposentado) |
| `cbor` | Ocupação/Profissão | `"CBOR"` |
| `infehosp` | Casos de infecção hospitalar | `"INFEHOSP"` |
| `diagnosticos_secundarios` | Comorbidades adicionais | `"codigo_cid_secundario"` |

---

## 🔗 Mapa de Relacionamentos (Joins)


* **Hospital:** `internacoes."CNES" = hospital."CNES"`
* **Município:** `internacoes."MUNIC_RES" = municipios."codigo_6d"`
* **Causa da Morte:** `mortes."CID_MORTE" = cid10."CID"`
* **Pré-natal:** `internacoes."N_AIH" = obstetricos."N_AIH"`