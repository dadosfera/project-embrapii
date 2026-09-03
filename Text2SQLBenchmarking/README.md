# Text2SQLBenchmarking

O **Text2SQLBenchmarking** é um benchmark de Text-to-SQL em português. A partir
de uma pergunta em linguagem natural, um modelo gera SQL; a consulta gerada e a
consulta de referência são executadas no banco correspondente, comparadas e
avaliadas por 13 conceitos métricos.

O projeto oferece duas formas complementares de uso:

- um pipeline científico batch, com geração, execução, avaliação e análise;
- uma interface web para Chat SQL e operação do Benchmark.

A interface reutiliza o pipeline e os mesmos artefatos. Ela não altera a
metodologia científica nem substitui os scripts e o notebook de análise.

## Principais recursos

- geração e avaliação de SQL nas bases PostgreSQL entregues;
- bibliotecas RawModel, VannaAI, PremSQLAgent e XiYanSQL;
- contextos sem contexto, documentação, exemplos ou ambos, conforme a
  biblioteca;
- Chat SQL somente leitura, com validação estrutural e limite de resultado;
- Benchmark com detecção de etapas faltantes, reexecução confirmada e histórico;
- Acurácia de Execução (EX) e 12 métricas adicionais persistidas por consulta;
- execução recomendada por Docker Compose, com backend CUDA e frontend nginx;
- persistência de modelos, resultados, journal e cache Chroma no host.

## Arquitetura em resumo

```text
pergunta + configuração
        |
        v
gerador Text-to-SQL
        |
        v
SQL gerada + SQL de referência
        |
        v
execução no banco real
        |
        v
comparação + 13 métricas
        |
        v
Parquets -> interface / notebook de análise
```

As duas bases incluídas no entregável e expostas pela interface são
`sih_database` (SIH/DataSUS) e `datasus` (JABUTI-SQL), ambas PostgreSQL.

## Início rápido com Docker

Requisitos: Linux, Docker Engine com plugin Compose e, para inferência local,
driver NVIDIA com NVIDIA Container Toolkit/CDI.

```bash
cd ~/Text2SQLBenchmarking
cp .env.example .env
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export PROJECT_ROOT="$PWD"
mkdir -p local_models resources/out interface/.runtime/chroma-cache
docker compose build
docker compose up -d
docker compose ps
```

A interface escuta em `127.0.0.1:5173` e o backend em
`127.0.0.1:8000`. Em um servidor remoto, encaminhe apenas o frontend:

```bash
ssh -N -L 5173:127.0.0.1:5173 <usuario>@<servidor>
```

Depois, abra `http://127.0.0.1:5173` no computador local. Antes de iniciar
Chat ou Benchmark, configure os bancos e, quando necessário, `HF_TOKEN` no
`.env` local. Geração e Benchmark podem usar GPU por longos períodos, baixar
modelos e gravar Parquets; não os use como teste de instalação.

## Documentação

- [Índice da documentação](docs/README.md)
- [Visão geral e estrutura do projeto](docs/VISAO_GERAL_E_ESTRUTURA.md)
- [Instalação e Docker](docs/INSTALACAO_E_DOCKER.md)
- [Interface: Chat SQL e Benchmark](docs/INTERFACE.md)
- [Pipeline científico e scripts](docs/BENCHMARK.md)
- [Análise e testes](docs/ANALISE_E_TESTES.md)
- [Modelos, bibliotecas, contextos e seeds](docs/MODELOS_BIBLIOTECAS_CONTEXTOS.md)
- [Datasets e bancos de dados](docs/BANCOS_DE_DADOS.md)
- [Métricas](docs/METRICAS.md)
- [Artefatos, Parquets, history e journal](docs/ARTEFATOS_E_RESULTADOS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

