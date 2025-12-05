FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema para o Reflex
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação primeiro
COPY rxconfig.py .
COPY frontend/ ./frontend/

# Inicializa o Reflex usando template blank automaticamente
RUN echo "0" | reflex init || true

# Variáveis de ambiente
ENV API_URL=http://backend:8000

# Expõe porta
EXPOSE 3000

# Comando de inicialização
CMD ["reflex", "run", "--env", "prod", "--backend-host", "0.0.0.0"]

