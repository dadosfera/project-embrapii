# Dashboard Dados em Saúde

Dashboard web para análise de dados de saúde armazenados em PostgreSQL.

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Recharts, TanStack Table e D3.
- **Backend:** Python, FastAPI e psycopg.
- **Produção:** Docker Compose, Nginx e imagens independentes para frontend e backend.
- **Banco:** PostgreSQL externo, acessado diretamente ou por túnel SSH.

## Execução com Docker — recomendada

### Pré-requisitos

- Docker Engine 24 ou superior.
- Docker Compose v2 (`docker compose`).
- Acesso de rede ao PostgreSQL utilizado pelo projeto.

Não é necessário instalar Node.js ou Python na máquina de hospedagem.

### 1. Configure o banco de dados

Na raiz do projeto:

```bash
cp .env.example .env
```

Edite o `.env` da raiz com as credenciais reais:

```env
DB_HOST=host.docker.internal
DB_PORT=5433
DB_NAME=nome_do_banco
DB_USER=usuario
DB_PASSWORD=senha
CORS_ORIGINS=http://localhost:8080
```

Use o endereço real do PostgreSQL em `DB_HOST` quando o banco for diretamente
acessível pela máquina. Use `host.docker.internal` quando o banco estiver
disponível por um túnel aberto na máquina que executa o Docker.

> O arquivo `.env` contém segredos, é ignorado pelo Git e não é copiado
> para as imagens.

### 2. Suba a aplicação

```bash
docker compose up --build -d
```

Abra:

```text
http://localhost:8080
```

Em outra máquina da rede, substitua `localhost` pelo IP ou domínio do servidor.
Para publicar em outra porta:

```bash
DASHBOARD_PORT=80 docker compose up --build -d
```

Libere somente essa porta no firewall. O backend permanece disponível apenas na
rede interna do Compose; o Nginx encaminha as requisições `/api` para ele.

### 3. Operação

```bash
# Ver estado e healthchecks
docker compose ps

# Acompanhar logs
docker compose logs -f

# Reiniciar os serviços
docker compose restart

# Atualizar após receber uma nova versão
docker compose up --build -d

# Encerrar
docker compose down
```

O healthcheck público do frontend está em `http://localhost:8080/health`.
O healthcheck do backend é executado internamente pelo Compose.

## PostgreSQL por túnel SSH

O processo SSH continua sendo executado no host, fora dos contêineres. O túnel
precisa aceitar conexões vindas da bridge do Docker, e `DB_HOST` deve ser
`host.docker.internal`.

Exemplo genérico:

```bash
ssh -g -L 0.0.0.0:5433:localhost:5432 usuario@servidor
```

Ajuste o destino e as portas à infraestrutura real. Restrinja o acesso à porta
do túnel no firewall do host; ela não deve ser publicada na internet.

Para testar a conexão a partir do backend:

```bash
docker compose exec backend python -c \
  "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health/database').read().decode())"
```

## Desenvolvimento sem Docker

### Backend

Requer Python 3.11 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- Documentação: `http://127.0.0.1:8000/docs`
- Banco: `http://127.0.0.1:8000/health/database`

Para execução local sem Docker, altere `DB_HOST` em `backend/.env` para o host
apropriado — normalmente `127.0.0.1` quando há um túnel local.

### Frontend

Requer Node.js 20.19 ou superior.

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Frontend: `http://localhost:5173`

O arquivo `frontend/.env.example` aponta para a API local. Na imagem de produção,
o frontend usa a mesma origem e o proxy `/api` do Nginx automaticamente.

## Estrutura de implantação

```text
Navegador :8080
      │
      ▼
Nginx / React
      │ /api
      ▼
FastAPI :8000 (rede interna)
      │
      ▼
PostgreSQL externo ou túnel no host
```
