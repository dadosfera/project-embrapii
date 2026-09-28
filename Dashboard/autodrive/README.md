# Chat Autodrive no Dashboard

Assistente **EMBRAPII · Analista DATASUS** no Autodrive STG standalone (`autodrive-assistant-api-standalone.stg.dadosfera.ai`),
embutido no data app como widget flutuante (todas as telas; contexto rico em Medicamentos). IDs em `autodrive_manifest.json`.

## Peças
| peça | onde | o quê |
|---|---|---|
| Knowledge base | `kb/` ← `build_kb.py` | 11 CSVs agregados do Snowflake `EMBRAPII_DATASUS` + `README_dicionario.md` (sobe como .txt) |
| Assistente | `setup_autodrive.py` | cria/atualiza KB e assistente (`charts` + `tables`, `gemini-2.5-pro`); rankings curtos embutidos nas instruções, porque o RAG nem sempre traz o trecho certo do CSV |
| Token + proxy | `backend/api/autodrive.py` | `POST /api/autodrive/chat-token`, `GET /api/autodrive/config`, `/api/autodrive/proxy/*` (same-origin; Origin fixo em host já liberado na allowlist do Autodrive) |
| Widget | `frontend/src/components/AutodriveChat.tsx` | carrega o bundle do STG e monta com `uiContextProvider` |
| Contexto da tela | `frontend/src/lib/uiContext.ts` | variáveis publicadas com `useUiContext()` + texto dos elementos `data-chat-context="rótulo"` → `ui_context` |

## Contexto da tela (Medicamentos)
`selection` (CATMAT carregado), `visible_kpis`, `filters` e `visible_data` com as séries dos gráficos: estoque por UF, fornecedores
e fabricantes vão brutos; evolução de preço vai bruta até 60 pontos (acima disso, média anual); o histórico de compras (até 500
linhas) vai resumido por ano × tipo + as 15 compras mais recentes. `page_text` leva título, subtítulo, KPIs, medicamento e alerta de lotes.

## Ajustes do proxy à versão do STG
O widget do STG só desenha `horizontal_bar`; a API às vezes devolve `bar_horizontal` (bloco vazio). O proxy renomeia o tipo e
remove do texto o JSON `<chart-plus-json>` e imagens markdown que o modelo às vezes repete quando já existe `response_blocks`.

## Comandos (a partir de `Dashboard/`)
```bash
set -a; source .env; set +a; export DB_ENGINE=snowflake SNOWFLAKE_DATABASE=DADOSFERA_PRD_DADOSFERADEMO
.venv/bin/python autodrive/build_kb.py                         # regenera kb/
AUTODRIVE_CORE_USER=admin AUTODRIVE_CORE_PASSWORD=<USER_ID do deployment> .venv/bin/python autodrive/setup_autodrive.py
AUTODRIVE_AUTH_CLIENT_ID=… AUTODRIVE_AUTH_CLIENT_SECRET=… .venv/bin/python autodrive/ask.py "pergunta" 1482   # testa com o contexto de um CATMAT
```
Mudou a KB? Troque `AUTODRIVE_KB_NAME` (a API não apaga dataset) e rode o setup: o assistente é atualizado no lugar (id do manifest).
Credenciais do client: secret `autodrive-secrets` do ns `autodrive-standalone` (cluster `platform-stg`); no deploy vão para as variáveis
do projeto Orchest com `deploy/deploy_service.py --autodrive-env-file <arquivo KEY=VALUE fora do repo>`.

Teste de ponta a ponta (usa o LLM): `E2E_CHAT=1 E2E_BASE_URL=<url>/ npx playwright test e2e/chat.spec.ts`.
