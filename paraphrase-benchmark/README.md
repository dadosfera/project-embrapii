# Paraphrase Benchmark

Aplicação para avaliar a qualidade de paráfrases e gerar pares NL-SQL usando LLMs.

## Funcionalidades

### Avaliação de Paráfrases
Avalie a qualidade de paráfrases usando três métricas complementares:

- **Cross-Encoder**: Similaridade semântica profunda (0-1)
- **SBERT**: Similaridade via embeddings de sentenças (0-1)
- **BLEU**: Sobreposição de n-gramas (0-100, menor = mais diverso)

### Pipeline de Geração NL-SQL (Novo!)
Gere datasets de pares pergunta/SQL automaticamente:

1. **Schema Input**: Cole o DDL do seu banco de dados
2. **Geração de Perguntas**: LLM gera ~50 perguntas relevantes
3. **Curadoria**: Selecione e edite as melhores perguntas
4. **Geração de SQL**: LLM gera queries SQL correspondentes
5. **Paráfrases**: Gere variações das perguntas
6. **Avaliação**: Métricas de qualidade das paráfrases

## Stack Técnica

| Camada | Tecnologia |
|--------|------------|
| Frontend | Reflex 0.6 |
| API | FastAPI |
| LLM | OpenAI GPT-4 |
| Avaliação | sentence-transformers, sacrebleu |
| Banco | SQLite + SQLAlchemy |
| Container | Docker Compose |

## Início Rápido

### Configuração da API Key

Para usar o Pipeline de Geração, configure sua chave da OpenAI:

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### Com Docker Compose (Recomendado)

```bash
cd paraphrase-benchmark

# Sobe toda a stack
OPENAI_API_KEY=$OPENAI_API_KEY docker compose up -d --build

# Acompanha os logs
docker compose logs -f
```

Aguarde o backend carregar os modelos (pode levar alguns minutos na primeira vez).

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8001/docs
- **API**: http://localhost:8001

### Desenvolvimento Local

#### Backend

```bash
cd backend

# Cria ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instala dependências
pip install -r requirements.txt

# Roda o servidor
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Cria ambiente virtual
python -m venv venv
source venv/bin/activate

# Instala dependências
pip install -r requirements.txt

# Inicializa o Reflex
reflex init

# Roda o servidor de desenvolvimento
reflex run
```

## Endpoints da API

### Avaliação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/evaluate` | Avalia pares e salva no histórico |
| GET | `/api/history` | Lista avaliações anteriores |
| GET | `/api/history/{id}` | Detalhes de uma avaliação |
| DELETE | `/api/history/{id}` | Remove avaliação |
| GET | `/api/health` | Health check |

### Pipeline de Geração

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/pipeline/generate-questions` | Gera perguntas a partir do schema |
| POST | `/api/pipeline/generate-sql` | Gera SQLs para perguntas curadas |
| POST | `/api/pipeline/generate-paraphrases` | Gera paráfrases das perguntas |
| POST | `/api/pipeline/regenerate-sql` | Regenera SQLs para paráfrases |
| GET | `/api/pipeline/sessions` | Lista sessões do pipeline |
| GET | `/api/pipeline/sessions/{id}` | Detalhes de uma sessão |
| DELETE | `/api/pipeline/sessions/{id}` | Remove uma sessão |

### Exemplo de Uso

```bash
curl -X POST "http://localhost:8001/api/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "pairs": [
      {
        "original": "Quantos casos de dengue foram registrados em 2023?",
        "paraphrase": "Qual o número de ocorrências de dengue no ano de 2023?"
      }
    ]
  }'
```

## Exemplos de Schema para o Pipeline

Copie e cole um desses schemas no Pipeline para testar a geração de perguntas NL-SQL:

### E-commerce

```sql
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    cidade VARCHAR(80),
    estado VARCHAR(2),
    data_cadastro DATE,
    total_compras DECIMAL(12,2)
);

CREATE TABLE produtos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200),
    categoria VARCHAR(50),
    preco DECIMAL(10,2),
    estoque INTEGER,
    avaliacao_media DECIMAL(3,2)
);

CREATE TABLE pedidos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    data_pedido TIMESTAMP,
    status VARCHAR(20),
    valor_total DECIMAL(12,2),
    frete DECIMAL(8,2)
);

CREATE TABLE itens_pedido (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER REFERENCES pedidos(id),
    produto_id INTEGER REFERENCES produtos(id),
    quantidade INTEGER,
    preco_unitario DECIMAL(10,2)
);
```

### Saúde Pública (DataSUS)

```sql
CREATE TABLE leitos (
    id SERIAL PRIMARY KEY,
    nome_hospital VARCHAR(255),
    cnes VARCHAR(20),
    uf_hospital VARCHAR(2),
    municipio_hospital VARCHAR(100),
    UTI_sus_adulto INTEGER,
    UTI_sus_neonatal INTEGER,
    leitos_geral INTEGER,
    data_competencia VARCHAR(10)
);

CREATE TABLE compras_medicamentos (
    id SERIAL PRIMARY KEY,
    descricao_catmat TEXT,
    preco_unitario DECIMAL(15,2),
    quantidade INTEGER,
    ano_compra INTEGER,
    fornecedor VARCHAR(255),
    municipio VARCHAR(100),
    uf VARCHAR(2)
);

CREATE TABLE estabelecimentos (
    cnes VARCHAR(20) PRIMARY KEY,
    nome_fantasia VARCHAR(255),
    tipo_estabelecimento VARCHAR(100),
    uf VARCHAR(2),
    municipio VARCHAR(100),
    natureza_juridica VARCHAR(100)
);
```

### RH / Funcionários

```sql
CREATE TABLE departamentos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100),
    orcamento_anual DECIMAL(15,2),
    gerente_id INTEGER
);

CREATE TABLE funcionarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150),
    email VARCHAR(150),
    cargo VARCHAR(100),
    departamento_id INTEGER REFERENCES departamentos(id),
    salario DECIMAL(12,2),
    data_admissao DATE,
    data_demissao DATE
);

CREATE TABLE avaliacoes (
    id SERIAL PRIMARY KEY,
    funcionario_id INTEGER REFERENCES funcionarios(id),
    ano INTEGER,
    nota DECIMAL(3,2),
    comentario TEXT,
    avaliador_id INTEGER REFERENCES funcionarios(id)
);

CREATE TABLE ferias (
    id SERIAL PRIMARY KEY,
    funcionario_id INTEGER REFERENCES funcionarios(id),
    data_inicio DATE,
    data_fim DATE,
    dias_utilizados INTEGER
);
```

### Educação

```sql
CREATE TABLE escolas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200),
    tipo VARCHAR(50),
    uf VARCHAR(2),
    municipio VARCHAR(100),
    ideb DECIMAL(3,2),
    total_alunos INTEGER
);

CREATE TABLE turmas (
    id SERIAL PRIMARY KEY,
    escola_id INTEGER REFERENCES escolas(id),
    serie VARCHAR(20),
    turno VARCHAR(20),
    ano_letivo INTEGER,
    total_alunos INTEGER
);

CREATE TABLE alunos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150),
    turma_id INTEGER REFERENCES turmas(id),
    data_nascimento DATE,
    media_geral DECIMAL(4,2),
    frequencia DECIMAL(5,2)
);

CREATE TABLE professores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150),
    escola_id INTEGER REFERENCES escolas(id),
    disciplina VARCHAR(50),
    formacao VARCHAR(100),
    anos_experiencia INTEGER
);
```

## Interpretação das Métricas

| Métrica | Bom Resultado | Interpretação |
|---------|---------------|---------------|
| Cross-Encoder | > 0.7 | Alta similaridade semântica |
| SBERT | > 0.8 | Embeddings muito próximos |
| BLEU | 15-40 | Diversidade estrutural adequada |

**Objetivo ideal**: SBERT e Cross-Encoder altos (mantém significado) + BLEU baixo (diversidade lexical).

## Estrutura do Projeto

```
paraphrase-benchmark/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── database.py       # SQLite config
│   │   ├── evaluator.py      # Lógica de avaliação
│   │   ├── llm_client.py     # Cliente OpenAI para geração
│   │   └── routes/
│   │       ├── evaluate.py   # Endpoints de avaliação
│   │       └── pipeline.py   # Endpoints do pipeline
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── frontend/
│   │   ├── frontend.py       # Reflex app
│   │   ├── state.py          # Estado global
│   │   └── components/
│   │       ├── evaluation_form.py
│   │       ├── history_table.py
│   │       └── pipeline/     # Componentes do pipeline
│   │           ├── pipeline_wizard.py
│   │           ├── schema_input.py
│   │           ├── question_curator.py
│   │           ├── sql_generator.py
│   │           ├── paraphrase_view.py
│   │           └── evaluation_step.py
│   ├── rxconfig.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Licença

MIT

