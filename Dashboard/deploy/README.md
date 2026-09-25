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
`--dry-run` lista o pipeline e os arquivos do upload; `--skip-upload` só recria o serviço (DELETE + create, URL estável).
O resultado (UUIDs e `dataapp_url`) fica em `deploy/manifest.json`, sem segredos.

**Variáveis do serviço**: `DB_ENGINE=snowflake`, `SNOWFLAKE_SECRET_ID=prd/root/snowflake_credentials/dadosferademo`,
`SNOWFLAKE_DATABASE=DADOSFERA_PRD_DADOSFERADEMO`, `SNOWFLAKE_SCHEMA=EMBRAPII_DATASUS`, `FRONTEND_DIST=/project-dir/frontend/dist`,
`APP_BASE_PATH=/$BASE_PATH_PREFIX_8000`, `QUERY_CACHE_TTL_SECONDS=3600`.

**Smoke** (o Orchest exige SSO): `python3 deploy/sso_storage_state.py /tmp/sso.json` (fora do repo; carrega token), depois
`cd frontend && E2E_STORAGE_STATE=/tmp/sso.json E2E_BASE_URL="<dataapp_url>" npx playwright test`.
