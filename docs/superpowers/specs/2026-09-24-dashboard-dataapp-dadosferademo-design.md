# Dashboard Dados em Saúde como data app no dadosferademo — design

Data: 24/09/2026 · Autor: Allan Sene · Branch: `feat/dadosfera-dataapp`

## Objetivo

Publicar o `Dashboard/` (React/Vite + FastAPI) como data app no Módulo de Inteligência do tenant `dadosferademo` (cluster **demo2**), lendo uma cópia dos dados DATASUS no Snowflake do tenant, com a identidade visual Beast e uma revisão de UX aprovada antes da implementação.

Fora do escopo: PAIRS (projeto separado, depois), Text2SQLBenchmarking, carga recorrente/CDC, endpoints novos.

## Contexto encontrado

- O backend lê um PostgreSQL 14 da UFMG (`150.164.2.13:5432`) acessível só por túnel SSH no bastion `150.164.2.44`. O cluster não alcança essa rede. O servidor tem `datalake_db` a `datalake_db4`; **o do Dashboard é o `datalake_db2`** (40 GB), o único com todas as tabelas citadas pelos routers, inclusive `cnpj_enriquecido`. Usuário `datalake_user` (confirmado em 24/09/2026 pelo túnel).
- Do `datalake_db2`, 39 GB são uma tabela só: `instituicao_estoca_produto` (248 M linhas). O resto soma ~1,2 GB.
- 28 endpoints em 4 routers (`compras`, `fornecedores`, `leitos`, `medicamentos`), ~2,5 mil linhas de SQL com sintaxe Postgres (`FILTER`, `JOIN LATERAL`, `BTRIM`, `::date`, `%(x)s`).
- `frontend/src/lib/api.ts` nunca foi commitado: a regra `lib/` do `Dashboard/.gitignore` (bloco Python) o ignora. O front não builda a partir do repo.
- O `BrowserRouter` não tem `basename` e o GeoJSON é buscado em `/maps/...` com caminho absoluto. Os dois quebram sob o prefixo `/pbp-service-…/` do Orchest.
- A imagem do Orchest (`dadosfera/base-kernel-py`) é Python 3.9. O backend usa `X | None` e pina FastAPI 0.141.
- `dados_datasus/README.md` expõe a senha do SSH em texto puro. É preciso avisar a UFMG para trocá-la; este trabalho não a reutiliza.

## Arquitetura

```
Postgres UFMG ──(túnel SSH, máquina do Allan)──► Dashboard/scripts/sync_snowflake.py
                                                   │ parquet → PUT/COPY
                                                   ▼
                                  Snowflake dadosferademo · EMBRAPII_DATASUS
                                                   ▼
             Mod. de Inteligência demo2 · standalone service `dataapp` :8000
             FastAPI (DB_ENGINE=snowflake) + front estático no mesmo processo
                                                   ▼
                                  Embed no Catálogo do app.dadosfera.ai
```

Arquivos novos ou alterados (tudo dentro de `Dashboard/`, sem repo novo):

| Caminho | Papel |
|---|---|
| `scripts/sync_snowflake.py` | Carga única Postgres → Snowflake |
| `backend/database.py` | Seleção de engine; `fetch_all`/`fetch_one` com a mesma assinatura |
| `backend/api/*.py` | SQL por engine no próprio router: `Q(pg=..., sf=...)` |
| `backend/cache.py` | Cache em memória com TTL + warm-up |
| `backend/main.py` | Serve `frontend/dist` com fallback SPA e injeta o prefixo |
| `tests/parity/` | Teste e relatório de paridade Postgres × Snowflake |
| `frontend/src/lib/api.ts`, `frontend/src/lib/fornecedoresApi.ts` | Clientes reconstruídos (os dois foram perdidos pelo `.gitignore`), porta única para a API |
| `frontend/src/index.css`, `components/Layout.tsx` | Tokens e shell Beast |
| `docs/ux-review/` | Report da revisão de UX (gate) |
| `deploy/` | `deploy_service.py`, `dadosfera_client.py`, `environment_setup.sh`, `manifest.json`, `verify.py` (padrão do OIC) |

## 1. Dados: Postgres → Snowflake

- **Tabelas:** o conjunto de tabelas e views citadas em `FROM`/`JOIN` nos routers. A lista é extraída por script e fixada em `scripts/tables.txt`, e o sync falha se um router citar algo fora dela. Views do Postgres viram tabelas no Snowflake. As CTEs (`kpis`, `ranqueado`, `snapshot_leitos` etc.) não são tabelas e ficam fora.
- **Recorte de `instituicao_estoca_produto`:** os três usos no backend (`medicamentos.py`: `resumo`, `lotes-vencendo`, `estoque-por-uf`) fazem `DISTINCT ON (instituicao_id)` ordenado por `data_de_posicao_no_estoque DESC NULLS LAST, instituicao_estoca_produto_id DESC`, então só a posição mais recente importa. O sync copia `SELECT DISTINCT ON (instituicao_id, produto_id) * ... ORDER BY instituicao_id, produto_id, data_de_posicao_no_estoque DESC NULLS LAST, instituicao_estoca_produto_id DESC` (~3,3 M linhas) com o mesmo nome de tabela. O resultado é exato: a linha que o backend escolhe por instituição é também a mais recente do seu par (instituição, produto) e sempre sobrevive ao recorte. O `mv_estoque_mais_recente` **não** serve: não tem a coluna `id` nem o desempate por `id`, e o `DESC` dele deixa NULLs primeiro. O sync grava o recorte em `sync_report.json` com as linhas de origem (total e recortado).
- **Fluxo:** para cada tabela, `COPY (SELECT *) TO` → parquet local → `PUT` no stage do schema → `CREATE OR REPLACE TABLE ... USING TEMPLATE` + `COPY INTO`. Nomes de colunas em minúscula no Postgres viram MAIÚSCULA sem aspas no Snowflake.
- **Idempotência:** cada execução recria as tabelas (`CREATE OR REPLACE`) e grava `scripts/sync_report.json` com as linhas na origem e no destino por tabela. O script termina com erro se alguma contagem divergir.
- **Credenciais:** SSH e Postgres vêm de `Dashboard/.env` (gitignored): `SSH_HOST`, `SSH_USER`, `SSH_PASSWORD`, `DB_*` com `DB_NAME=datalake_db2`. O Snowflake usa o secret da org Dadosfera `prd/root/snowflake_credentials/dadosferademo`. Nenhuma credencial de cliente ou da UFMG entra no repo nem no Orchest.
- **Schema:** `EMBRAPII_DATASUS`. O app usa o role do secret e o `database.py` recusa qualquer statement que não comece com `SELECT` ou `WITH`; não há role dedicado nesta entrega.

## 2. Backend dual-engine

- `DB_ENGINE=postgres` (default, comportamento atual para a UFMG) ou `snowflake`.
- Cada query vira `Q(pg=..., sf=...)` no próprio router (decisão do plano: tirar 2,5 mil linhas de SQL para arquivos deixaria o diff ilegível para a UFMG). O `pg` é o SQL atual sem alteração. O `sf` é o porte: o sqlglot gera o rascunho e cada arquivo é revisado à mão. Regras de porte:

| Postgres | Snowflake |
|---|---|
| `SUM(x) FILTER (WHERE c)` | `SUM(IFF(c, x, NULL))` |
| `BTRIM(s)` | `TRIM(s)` |
| `DATE_TRUNC('month', d)::date` | igual |
| `JOIN LATERAL (...)` | `QUALIFY ROW_NUMBER() OVER (...) = 1` ou `LATERAL` suportado |
| `%(nome)s` | `%(nome)s` (connector em `paramstyle=pyformat`) |

- Fragmentos de filtro montados por concatenação (ex.: `filtro_uf`) viram funções que recebem o `engine`.
- As chaves das linhas são normalizadas para minúscula no retorno do Snowflake, para que o JSON da API seja idêntico entre engines. `Decimal` e datas são serializados como hoje.
- **Compatibilidade com Python 3.9:** `from __future__ import annotations` nos módulos, `Optional` onde a anotação é avaliada em runtime (FastAPI/pydantic) e pins compatíveis (`fastapi==0.104.1`, `uvicorn==0.24.0`, `snowflake-connector-python>=3.7,<5`). O `psycopg` fica em extra opcional.
- **Cache:** respostas em memória por (endpoint, parâmetros), com TTL de 3600 s (`QUERY_CACHE_TTL_SECONDS`). No startup, o warm-up chama os endpoints da Home. Uma conexão Snowflake com lock (o cache absorve a carga da demo); pool só se a latência pedir.
- **Erros:** falha no banco → HTTP 503 com a mensagem do engine ativo, sem fallback para outro engine. `/health/database` informa `{"engine": ..., "status": ...}`.

### Paridade

`tests/parity/test_parity.py` roda na máquina do Allan com o túnel aberto. Para cada um dos 28 endpoints, chama o app com `DB_ENGINE=postgres` e `DB_ENGINE=snowflake` usando parâmetros fixos de `tests/parity/cases.yaml` (UFs, produtos, períodos e filtros usados pelas páginas, ao menos um caso por endpoint e um caso "sem filtro"). A comparação ordena as linhas por todas as colunas e compara numéricos com tolerância absoluta de 1e-6. Critério de aceite: 28/28 iguais. O resultado vai para `tests/parity/report.md`.

## 3. Front

### 3a. Base técnica
- `.gitignore`: `lib/` → `/lib/`, e o `frontend/src/lib/` passa a ser versionado.
- `src/lib/api.ts` reconstruído: todas as funções importadas pelas páginas (`buscarComprasPorMes`, `buscarKpisCompras`, `buscarPainelLeitos`, `listarProdutos` etc.), com tipos derivados das respostas reais. Um `request<T>(path, params)` central resolve a URL relativa ao prefixo e lança erro tipado. Nenhuma página chama `fetch` direto; o `MapaBrasil.tsx` também passa pelo helper de URL.
- Prefixo: Vite com `base: './'`. O FastAPI injeta `<base href="{APP_BASE_PATH}/">` e `window.__APP_BASE__` no `index.html` servido, e o `BrowserRouter` usa `basename={window.__APP_BASE__}`. Um único build serve qualquer prefixo; no `npm run dev` o prefixo é vazio.

### 3b. Beast
- Tokens do `:root` substituídos pelos do Beast: primary `#1700a2` e a paleta Beast, fonte Quicksand (via `@fontsource`), raios e sombras. Tema claro e escuro por tokens; chave de preferência `dashboard.theme`.
- Gráficos: paleta categórica e sequencial derivadas do Beast, com contraste validado nos dois temas, aplicada via um único `chartPalette` consumido por Recharts e pelo D3 do mapa.
- Shell (`Layout.tsx`): logo Dadosfera, crédito "Projeto EMBRAPII · DCC/UFMG", ícones Eva (SVG).

### 3c. Revisão de UX (gate)
- Report em `Dashboard/docs/ux-review/` (HTML Beast), com uma seção por página: print atual, problemas (hierarquia, KPIs, filtros, tabelas, estados vazio/erro/carregando), proposta com mockup e esforço.
- Nenhuma mudança de layout de página entra antes de o Allan aprovar o report. Propostas que exigem endpoint novo ficam listadas como pendência e não são implementadas.

### Testes do front
`tsc --noEmit`, `npm run build` e um smoke Playwright (as 6 páginas carregam, sem erro de console, com dado renderizado) contra o backend local e depois contra a URL do demo2.

## 4. Deploy e verificação

- `deploy/deploy_service.py`, adaptado do OIC (`kine-gest-ddf/apps/oic-visitors/deploy/`): login no Maestro com `DADOSFERADEMO_USER/PASSWORD` → projeto `embrapii-dashboard-datasus` no demo2 (`POST /async/projects` com `description`) → ambiente `base-kernel-py` + `environment_setup.sh` (poll em `/catch/api-proxy/api/environment-builds/most-recent/<project_uuid>`) → upload de `backend/` inteiro + `frontend/dist/` → pipeline com o serviço `dataapp` (porta 8000, `preserve_base_path`, env `DB_ENGINE=snowflake`, `SNOWFLAKE_SECRET_ID`, `SNOWFLAKE_SCHEMA=EMBRAPII_DATASUS`, `APP_BASE_PATH=/$BASE_PATH_PREFIX_8000`) → standalone service. Os UUIDs e a URL ficam em `deploy/manifest.json`.
- Upload: o script lista `backend/` recursivamente em vez de manter uma lista de arquivos à mão (lição do Porto: arquivo faltando → CrashLoopBackOff).
- `deploy/verify.py`: `/health`, `/health/database` com `engine=snowflake` e um GET por router com dado não vazio; roda o smoke Playwright contra a URL publicada.
- Catálogo: o data app entra como ativo no Catálogo do dadosferademo, com embed, tag `embrapii` e documentação em HTML Quill, seguindo o padrão Porto (adotar o ativo automático quando existir, nunca criar dataset à mão).

## Ordem de execução

1. Base: `.gitignore`, `api.ts`, prefixo, Python 3.9 (o front builda e roda local contra o Postgres).
2. Dados: `sync_snowflake.py` + relatório de contagens.
3. Backend: porte `.sf.sql` + paridade 28/28.
4. Deploy no demo2 + `verify.py` (visual atual; o app já fica acessível).
5. Report de UX → aprovação do Allan.
6. Beast + UX aprovada → redeploy → verify → Catálogo.
7. PR `feat/dadosfera-dataapp` → `main` no `project-embrapii`.

## Riscos

- **Túnel instável** (o README da UFMG avisa sobre timeout): o sync é por tabela e retomável, pulando as tabelas já carregadas com contagem batendo.
- **`JOIN LATERAL`/semântica de NULL** divergindo no porte: coberto pela paridade; nenhum endpoint vai para o deploy sem estar verde.
- **Volume:** medido em 24/09/2026 (~1,2 GB + recorte do estoque). O sync mede de novo antes da carga e, se passar de 5 GB, para e consulta o Allan. O `DISTINCT ON` sobre 248 M linhas usa o índice `idx_iep_inst_prod_data` e roda no servidor via `COPY (query) TO STDOUT`, então só o recorte trafega pelo túnel.
- **Futuro do cluster demo2** (housecleaning): o deploy é por script e idempotente, então a republicação em outro cluster é trocar a URL do Orchest.

## Decisões durante a execução

- **25/09/2026, desempate nos rankings (exceção à regra "PG byte a byte").** Os `ORDER BY` que alimentam `LIMIT` ou a escolha de campeão por `ROW_NUMBER`/`QUALIFY` ganharam desempate determinístico idêntico nas duas versões (`fornecedores`: ranking `, cnpj ASC`, top-por-uf `, fornecedor ASC`; `compras`: fornecedores, fabricantes, modalidades e tipos por nome `ASC`). Sem isso, empates davam resultado diferente entre engines e entre execuções. Commit `5c45780`. Empates residuais (mesmo CNPJ, collation `en_US` × binária em nomes acentuados) ficam registrados como risco conhecido: se aparecerem na paridade, usar `COLLATE "C"` no PG ou um id numérico como último critério.
- **25/09/2026, estoque não reexportado.** A amostra `TABLESAMPLE SYSTEM (0.1)` (249 mil linhas) não achou texto "NA"/"NULL"/"nan" nem string vazia nas colunas de texto de `instituicao_estoca_produto`; a carga com o parser antigo é fiel para essa tabela. O sync só inclui o estoque com `--include-stock`.
