# Visão geral e estrutura do projeto

## Finalidade

O Text2SQLBenchmarking avalia sistemas que transformam perguntas em português
em consultas SQL. A unidade do experimento é uma pergunta com SQL de referência,
base, biblioteca, modelo, contexto e seed. A geração produz um Parquet; a etapa
seguinte executa a referência e a SQL gerada, compara os resultados, calcula as
métricas e produz o Parquet executado.

A interface web acrescenta operação interativa sem substituir o pipeline:

- **Chat SQL:** gera e executa uma consulta somente leitura para uma pergunta;
- **Benchmark:** inspeciona artefatos, executa etapas faltantes e apresenta
  métricas agregadas.

## Componentes

```text
Text2SQLBenchmarking/
├── src/                         geradores, execução e métricas
│   └── vendor/m_schema/         M-Schema vendorizado para XiYanSQL
├── interface/
│   ├── backend/                 API, Chat, Benchmark, runtime e testes
│   └── frontend/                aplicação React/TypeScript e nginx
├── datasets/                    perguntas, referências e contextos entregues
├── resources/out/               Parquets ativos e históricos
├── local_models/                modelos Hugging Face locais
├── bash/                        wrappers batch
├── docs/                        documentação pública
├── run_sql_generate.py          geração batch
├── run_sql_execution.py         execução, comparação e métricas
├── run_analise.ipynb            análise dos Parquets executados
├── Dockerfile                   imagem Python/CUDA do backend
├── compose.yaml                 serviços backend e frontend
├── .env.example                 variáveis locais sem segredos
├── pyproject.toml               dependências e grupos Python
└── uv.lock                      lock reproduzível do ambiente Python
```

## Pastas e arquivos principais

### `src/`

Contém as implementações científicas:

- `rawmodel.py`, `vannaai.py`, `premsqlAgente.py` e `xiyansql.py`: geradores;
- `executor.py`: execução e comparação das consultas;
- `text2sql_metrics.py`: fórmulas das 12 métricas adicionais;
- `metric_contract.py`: nomes canônicos, códigos e colunas persistidas;
- `utilitis.py`: registry de bancos/modelos e helpers compartilhados;
- `vendor/m_schema/`: código vendorizado usado para representar schemas no
  XiYanSQL.

Esses módulos são usados pelos scripts batch e pelos adapters da interface.

### `interface/backend/`

É uma aplicação FastAPI com um worker. Os principais domínios são:

- `api/`: rotas, schemas HTTP e tratamento público de erros;
- `adapters/`: integração entre o catálogo e os geradores científicos;
- `chat/`: jobs efêmeros, validação somente leitura e execução PostgreSQL;
- `benchmark/`: artefatos, reexecução, journal, métricas agregadas e serviço;
- `runtime/`: carregamento, troca e liberação de um único runtime;
- `operations/`: exclusão de operações pesadas;
- `domain/`: catálogo, contratos de artefatos, erros e metadata;
- `tests/`: suíte isolada com mocks, fixtures e diretórios temporários.

### `interface/frontend/`

Aplicação React/TypeScript construída com Vite. Em produção, o bundle é servido
por nginx não-root em `127.0.0.1:5173`; requisições `/api/` são encaminhadas ao
backend em `127.0.0.1:8000`. `package.json` e `package-lock.json` definem o
ambiente npm, e `.nvmrc` seleciona Node 24.

### `datasets/`

Reúne somente as entradas científicas entregues para SIH/DataSUS e
JABUTI-SQL: ground truths, documentação semântica e exemplos few-shot. A lista exata está em
[Bancos de dados](BANCOS_DE_DADOS.md).

### `resources/out/`

Recebe os Parquets de geração e execução. Reexecuções confirmadas arquivam os
arquivos ativos em subdiretórios `history/`. O diretório é bind mount gravável
do container e deve ser preservado como resultado científico.

### `local_models/`

Cache persistente dos modelos baixados. O nome local deriva do ID Hugging Face,
substituindo barras por hífens. Esse diretório não faz parte da imagem nem do
Git.

### `bash/` e arquivos `run_*`

`bash/geracao.sh` e `bash/execucao.sh` percorrem arrays de configurações e
chamam, respectivamente, `run_sql_generate.py` e `run_sql_execution.py`.
`run_analise.ipynb` lê somente Parquets executados e agrega as métricas já
persistidas.

## Fluxos de dados

### Pipeline batch

```text
ground truth + contexto + modelo
              |
              v
run_sql_generate.py
              |
              v
Parquet de geração
              |
              v
run_sql_execution.py
              |
              v
Parquet executado com resultados operacionais e métricas
              |
              v
run_analise.ipynb
```

### Interface

O frontend consulta o catálogo e o estado do backend. Chat e Benchmark usam o
mesmo coordenador de operação e o mesmo gerenciador de runtime. O Chat mantém
jobs em memória; o Benchmark persiste snapshots de jobs no journal SQLite e
persiste resultados em Parquet.

## Entradas, saídas e estado operacional

| Tipo | Exemplos | Natureza |
| --- | --- | --- |
| entrada científica | ground truths, documentação e exemplos das duas bases | versionável no entregável |
| configuração local | `.env`, modelos, acesso PostgreSQL | privada, não versionável |
| saída científica | Parquets em `resources/out/` e `history/` | persistente, não versionável |
| estado operacional | journal, workspaces e cache Chroma em `interface/.runtime/` | persistente/recriável conforme o item |
| build local | `.venv`, `node_modules`, `dist` | recriável, não versionável |

## Limites atuais

- a interface expõe apenas as bases PostgreSQL `sih_database` e `datasus`;
- uma operação pesada é admitida por vez e não há fila;
- o Chat não usa histórico de mensagens como contexto;
- o Benchmark não retoma automaticamente um subprocesso após reinício;
- o deployment exige um worker backend;
- modelos, PostgreSQL, datasets pesados e resultados ficam fora das imagens.
