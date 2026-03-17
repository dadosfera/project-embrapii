
# Geração Text-to-SQL

## Configuração do Ambiente

### Pré-requisitos
- Python 3.10+
- uv (gerenciador de pacotes Python)

### Instalação

1. Crie um ambiente virtual com uv:
```bash
uv venv
source .venv/bin/activate

```

2. Instale as dependências com uv:
```bash
uv sync
```


3. Configuração de Credenciais:
Crie um arquivo .env na raiz do projeto e adicione seu token do Hugging Face:
```bash
HUGGINGFACE_TOKEN=seu_token_aqui
```

4. Para instalação do banco de dados SIH Datasus, consulte o [link](https://github.com/DAVINTLAB/DATASUSAnalytics/tree/main/database)

## Estrutura do Projeto

```
.
├── bash/
│   ├── geracao.sh           # Script para disparar a geração de SQL
│   └── execucao.sh          # Script para executar o SQL gerado nas bases de dados
├── resources/
│   ├── queries/             # Documentação e consultas das bases de dados
│   │   ├── datasus/         # Documentação e consultas das bases de dados do datasus que desenvolvemos 
│   │   ...
│   └── out/                 # Resultados gerados pelos modelos (JSON/SQL)
├── src/                     # Core: Implementações PremSQL e VannaAI
├── run_sql_generate.py      # Script principal para geração de consultas
├── run_sql_execution.py     # Script para execução e das consultas
├── run_analise.ipynb        # Notebook para cálculo de métricas (Ex: Execution Accuracy - EX)
...                          # Arquivos do uv para gerenciamento de bibliotecas
```

## Execução

### Geração dos SQL 

Configure os modelos, bibliotecas e bases de dados desejadas diretamente no script ```bash/geracao.sh```. Em seguida, execute:

```bash
bash bash/geracao.sh
```

### Execução dos SQL

Para testar a validade das consultas geradas frente ao banco de dados, configure o ```bash/execucao.sh``` com os parâmetros correspondentes e execute:

```bash
bash bash/execucao.sh
```

### Analise dos resultados 

O arquivo  ```run_analise.ipynb ``` é utilizado para gerar a metrica EX dos resultados.
