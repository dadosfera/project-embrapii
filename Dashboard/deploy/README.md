# Deploy no Módulo de Inteligência (demo2, tenant dadosferademo)

Sobe o Dashboard como standalone service do Orchest: projeto `embrapii-dashboard-datasus`, ambiente
`embrapii-dashboard` (base-kernel-py, Python 3.9, `environment_setup.sh`), pipeline `embrapii_dataapp` com o serviço `dataapp`.

**Pré-requisitos**
- `.env` com `DADOSFERADEMO_USER`/`DADOSFERADEMO_PASSWORD` (o do ai-cto-assistants), apontado por `DADOSFERA_ENV_FILE`.
- `frontend/dist` buildado a partir do HEAD: `cd frontend && npm run build` (sem prefixo; ele chega em runtime).

**Comandos** (a partir de `Dashboard/`)
```bash
DADOSFERA_ENV_FILE=/Users/allansene/Repos/dadosfera/ai-cto-assistants/.env .venv/bin/python deploy/deploy_service.py --start
DADOSFERA_ENV_FILE=/Users/allansene/Repos/dadosfera/ai-cto-assistants/.env .venv/bin/python deploy/verify.py
```
`--dry-run` lista o pipeline, o setup script e os arquivos do upload. `--skip-upload` pula o upload e segue o resto
(ambiente: rebuild se o script ou o sha256 do `requirements.txt` mudou ou se o último build não foi SUCCESS; pipeline; com `--start`,
DELETE + create do serviço, URL estável). Upload = `git ls-files backend` + `frontend/dist/**`; recusa `*.env`, `*.pem`, `*.key`, `*secret*`, `*credential*`.
O resultado (UUIDs e `dataapp_url`) fica em `deploy/manifest.json`, sem segredos.

**Variáveis do serviço**: `DB_ENGINE=snowflake`, `SNOWFLAKE_SECRET_ID=prd/root/snowflake_credentials/dadosferademo`,
`SNOWFLAKE_DATABASE=DADOSFERA_PRD_DADOSFERADEMO`, `SNOWFLAKE_SCHEMA=EMBRAPII_DATASUS`, `FRONTEND_DIST=/project-dir/frontend/dist`,
`APP_BASE_PATH=/$BASE_PATH_PREFIX_8000`, `QUERY_CACHE_TTL_SECONDS=3600`.

**Smoke** (o Orchest exige SSO; o JSON carrega token, então fica fora do repo, e o script recusa caminho dentro dele):
```bash
DADOSFERA_ENV_FILE=/Users/allansene/Repos/dadosfera/ai-cto-assistants/.env .venv/bin/python deploy/sso_storage_state.py /tmp/sso.json
cd frontend && E2E_STORAGE_STATE=/tmp/sso.json E2E_BASE_URL="<dataapp_url>" npx playwright test; rm /tmp/sso.json
```
