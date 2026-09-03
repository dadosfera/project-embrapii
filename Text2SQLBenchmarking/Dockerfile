# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.9.27 AS uv

FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=python3.10 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        libpq5 \
        python3.10 \
        python3.10-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /usr/local/bin/

WORKDIR /build

COPY pyproject.toml uv.lock README.md ./

# O grupo dev permanece para preservar nbclient/nbconvert usados na análise.
# O projeto é um conjunto de scripts, portanto não há pacote local a instalar.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --group interface --no-install-project

WORKDIR /app

COPY src/ ./src/
COPY interface/__init__.py ./interface/__init__.py
COPY interface/backend/ ./interface/backend/
COPY bash/ ./bash/
COPY run_sql_generate.py run_sql_execution.py run_analise.ipynb ./

# Usuários numéricos do host podem criar e remover somente seus workspaces
# temporários (vanna_storage/premsql) sem tornar o código root-owned editável.
RUN chmod 1777 /app

CMD ["uvicorn", "interface.backend.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
