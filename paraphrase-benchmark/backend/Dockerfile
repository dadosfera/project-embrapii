FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY app/ ./app/

# Cria diretório para o banco de dados
RUN mkdir -p /data

# Variáveis de ambiente
ENV DATABASE_URL=sqlite:////data/paraphrase_benchmark.db
ENV TRANSFORMERS_CACHE=/app/.cache

# Expõe porta
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]




