# Paraphrase Benchmark

Aplicação para avaliar a qualidade de paráfrases usando três métricas complementares:

- **Cross-Encoder**: Similaridade semântica profunda (0-1)
- **SBERT**: Similaridade via embeddings de sentenças (0-1)
- **BLEU**: Sobreposição de n-gramas (0-100, menor = mais diverso)

## Stack Técnica

| Camada | Tecnologia |
|--------|------------|
| Frontend | Reflex 0.6 |
| API | FastAPI |
| Avaliação | sentence-transformers, sacrebleu |
| Banco | SQLite + SQLAlchemy |
| Container | Docker Compose |

## Início Rápido

### Com Docker Compose (Recomendado)

```bash
cd paraphrase-benchmark

# Sobe toda a stack
docker compose up -d --build

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

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/evaluate` | Avalia pares e salva no histórico |
| GET | `/api/history` | Lista avaliações anteriores |
| GET | `/api/history/{id}` | Detalhes de uma avaliação |
| DELETE | `/api/history/{id}` | Remove avaliação |
| GET | `/api/health` | Health check |

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
│   │   └── routes/
│   │       └── evaluate.py   # Endpoints
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── frontend/
│   │   ├── frontend.py       # Reflex app
│   │   ├── state.py          # Estado global
│   │   └── components/
│   │       ├── evaluation_form.py
│   │       └── history_table.py
│   ├── rxconfig.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Licença

MIT

