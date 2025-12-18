FROM python:3.11-slim

# Java 21 para JDBC (compatível com Debian trixie)
RUN apt-get update && \
    apt-get install -y openjdk-21-jdk-headless curl && \
    apt-get clean

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

COPY . .

CMD ["python", "main.py"]
