# Dashboard DATASUS como data app — Plano A (base, dados, backend, deploy, report de UX)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar o `Dashboard/` no Mod. de Inteligência demo2 lendo do Snowflake `EMBRAPII_DATASUS`, com os 28 endpoints em paridade com o Postgres da UFMG, e entregar o report de revisão de UX para aprovação.

**Architecture:** O backend FastAPI ganha uma camada de engine (`DB_ENGINE=postgres|snowflake`) com SQL por engine dentro dos routers (`Q(pg=..., sf=...)`). Um script local copia o `datalake_db2` pelo túnel SSH para o Snowflake. O mesmo processo FastAPI serve o build do front sob o prefixo do Orchest. O deploy reaproveita o padrão do OIC.

**Tech Stack:** Python 3.9 (imagem Orchest) / 3.12 local, FastAPI 0.104, psycopg 3, snowflake-connector-python 3, pyarrow, React 19 + Vite 7 + react-router 7, Playwright.

**Spec:** `docs/superpowers/specs/2026-09-24-dashboard-dataapp-dadosferademo-design.md`. O Plano B (Beast + UX aprovada + Catálogo) é escrito depois que o Allan aprovar o report da Task 17.

**Convenções deste plano**
- Repo: `/Users/allansene/Repos/dadosfera/project-embrapii`, branch `feat/dadosfera-dataapp`. Todos os caminhos são relativos a `Dashboard/`, salvo indicação.
- Os comandos Python rodam na raiz `Dashboard/` com o venv `Dashboard/.venv` (Task 2).
- Pip e npm globais apontam para um CodeArtifact com credencial expirada. Use sempre `PIP_CONFIG_FILE=/dev/null pip install -i https://pypi.org/simple ...` e `npm ... --registry=https://registry.npmjs.org/`.
- Nunca commite `.env`, `.secrets/`, parquet ou `sync_report.json`.

## Mapa de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `.gitignore` | `lib/` → `/lib/` |
| `backend/requirements.txt` | pins compatíveis com 3.9 |
| `backend/database.py` | engine, `Q`, `fetch_all`/`fetch_one`, guarda SELECT-only, normalização de chaves |
| `backend/snowflake_conn.py` | conexão Snowflake a partir do secret (arquivo local ou AWS SM) |
| `backend/cache.py` | cache TTL em memória |
| `backend/static.py` | serve `frontend/dist` com fallback SPA e injeção do prefixo |
| `backend/main.py` | liga static, warm-up e `/health/database` com engine |
| `backend/api/*.py` | queries viram `Q(pg, sf)`; fragmentos recebem `engine` |
| `backend/tests/` | testes unitários (pytest) |
| `scripts/tunnel.sh` | abre o túnel SSH (expect) |
| `scripts/tables.txt` | tabelas copiadas |
| `scripts/sync_snowflake.py` | carga Postgres → Snowflake |
| `tests/parity/cases.yaml`, `tests/parity/test_parity.py` | paridade dos 28 endpoints |
| `frontend/vite.config.ts` | `base: './'` |
| `frontend/src/lib/base.ts` | prefixo em runtime, `apiUrl()`, `assetUrl()` |
| `frontend/src/lib/api.ts`, `frontend/src/lib/fornecedoresApi.ts` | clientes reconstruídos |
| `frontend/src/main.tsx`, `frontend/src/components/MapaBrasil.tsx` | `basename` e URL do GeoJSON |
| `frontend/e2e/smoke.spec.ts`, `frontend/playwright.config.ts` | smoke das 6 páginas |
| `deploy/*` | deploy no Orchest demo2 (padrão OIC) |
| `docs/ux-review/` | report de UX (gate) |

---

### Task 1: `.gitignore` libera `frontend/src/lib/`

**Files:** Modify: `.gitignore` (linha 91, bloco "Build / empacotamento Python")

- [ ] **Step 1: Confirmar o problema**

Run: `git check-ignore -v frontend/src/lib/api.ts`
Expected: `.gitignore:91:lib/	frontend/src/lib/api.ts`

- [ ] **Step 2: Trocar `lib/` por `/lib/` e `lib64/` por `/lib64/`**

```gitignore
/lib/
/lib64/
```

- [ ] **Step 3: Verificar**

Run: `git check-ignore -v frontend/src/lib/api.ts; echo "exit=$?"`
Expected: sem saída e `exit=1` (não ignorado).

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "fix(dashboard): gitignore de lib/ engolia frontend/src/lib"
```

---

### Task 2: Backend compatível com Python 3.9 e venv

**Files:** Modify: `backend/requirements.txt`, `backend/api/compras.py`, `backend/api/leitos.py`, `backend/api/medicamentos.py`, `backend/api/fornecedores.py`, `backend/database.py`

O FastAPI avalia as anotações dos endpoints em runtime, e no 3.9 `int | None` quebra mesmo com `from __future__ import annotations`. Troque por `Optional[...]`.

- [ ] **Step 1: Pins**

`backend/requirements.txt`:

```text
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
psycopg[binary]==3.2.3
python-dotenv==1.0.1
snowflake-connector-python>=3.7,<4
cryptography>=41,<46
boto3>=1.28,<2
pyyaml>=6,<7
```

Crie `backend/requirements-dev.txt`:

```text
-r requirements.txt
pytest==8.3.3
httpx==0.27.2
pyarrow>=15,<18
```

(`httpx` 0.28 quebra o TestClient do starlette dessa versão, então fica pinado em 0.27.)

- [ ] **Step 2: Achar a sintaxe 3.10+**

Run: `grep -nE "\b[A-Za-z_\]]+ \| None|\bdict\[|\blist\[|\btuple\[" backend/*.py backend/api/*.py`
Expected: ocorrências como `catmat_id: int | None = Query(...)`, `-> tuple[str, dict]`, `dict[str, Any] | None`.

- [ ] **Step 3: Substituir**

Em cada arquivo listado: adicione `from typing import Any, Dict, List, Optional, Tuple` e troque `X | None` → `Optional[X]`, `dict[...]` → `Dict[...]`, `list[...]` → `List[...]` e `tuple[...]` → `Tuple[...]`. Exemplo em `compras.py`:

```python
def _montar_filtros(
    data_inicio: date,
    data_fim: date,
    catmat_id: Optional[int],
    tipo_compra: str,
) -> Tuple[str, Dict]:
```

- [ ] **Step 4: Venv e import no 3.9**

```bash
python3.12 -m venv .venv
PIP_CONFIG_FILE=/dev/null .venv/bin/pip install -q -i https://pypi.org/simple -r backend/requirements-dev.txt
docker run --rm -v "$PWD":/app -w /app python:3.9-slim bash -c \
  "pip install -q -r backend/requirements.txt && python -c 'import backend.main; print(\"ok\")'"
```

Expected: `ok` (o import não conecta no banco).

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "chore(dashboard): backend compativel com Python 3.9 (imagem do Orchest)"
```

---

### Task 3: Camada de engine (`database.py`)

**Files:** Modify: `backend/database.py`; Create: `backend/snowflake_conn.py`, `backend/tests/__init__.py`, `backend/tests/test_database.py`

Contrato (os routers dependem disso):
- `get_engine() -> str` lê `DB_ENGINE` (default `postgres`; valores aceitos `postgres`/`snowflake`).
- `Q(pg: str, sf: Optional[str] = None)` é um SQL com uma versão por engine. `Q.for_engine(engine)` devolve o texto; sem `sf`, o engine `snowflake` levanta `NotImplementedError("query sem versão Snowflake")`.
- `fetch_all(query: Union[str, Q], params=None) -> List[dict]` e `fetch_one(...) -> Optional[dict]`: uma `str` é tratada como `Q(pg=str)`, e as chaves voltam em minúscula.
- Guarda: o texto, sem comentários e espaços iniciais, precisa começar com `SELECT` ou `WITH`; caso contrário, `ValueError`.
- `DatabaseError` é a exceção única que os routers capturam (envolve `psycopg.Error` e `snowflake.connector.Error`).

- [ ] **Step 1: Testes que falham**

`backend/tests/test_database.py`:

```python
import pytest

from backend import database
from backend.database import Q


def test_q_escolhe_texto_por_engine():
    q = Q(pg="SELECT 1", sf="SELECT 2")
    assert q.for_engine("postgres") == "SELECT 1"
    assert q.for_engine("snowflake") == "SELECT 2"


def test_q_sem_sf_falha_no_snowflake():
    with pytest.raises(NotImplementedError):
        Q(pg="SELECT 1").for_engine("snowflake")


def test_engine_default_e_invalido(monkeypatch):
    monkeypatch.delenv("DB_ENGINE", raising=False)
    assert database.get_engine() == "postgres"
    monkeypatch.setenv("DB_ENGINE", "oracle")
    with pytest.raises(RuntimeError):
        database.get_engine()


@pytest.mark.parametrize("sql", ["DELETE FROM x", "  update x set a=1", "-- c\nDROP TABLE x"])
def test_guarda_select_only(sql):
    with pytest.raises(ValueError):
        database._assert_read_only(sql)


@pytest.mark.parametrize("sql", ["SELECT 1", "\n  -- comentario\n  WITH a AS (SELECT 1) SELECT * FROM a"])
def test_guarda_aceita_leitura(sql):
    database._assert_read_only(sql)


def test_fetch_all_normaliza_chaves(monkeypatch):
    monkeypatch.setenv("DB_ENGINE", "snowflake")
    monkeypatch.setattr(database, "_run", lambda engine, sql, params: [{"UF": "MG", "VALOR_TOTAL": 1}])
    assert database.fetch_all(Q(pg="SELECT 1", sf="SELECT 1")) == [{"uf": "MG", "valor_total": 1}]


def test_fetch_one_vazio(monkeypatch):
    monkeypatch.setattr(database, "_run", lambda engine, sql, params: [])
    assert database.fetch_one("SELECT 1") is None
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest backend/tests/test_database.py -q`
Expected: FAIL (`ImportError: cannot import name 'Q'`).

- [ ] **Step 3: `backend/snowflake_conn.py`**

```python
"""Conexão Snowflake do dadosferademo.

Credenciais: SNOWFLAKE_SECRET_FILE (JSON local) ou SNOWFLAKE_SECRET_ID (AWS Secrets Manager, dentro do
Módulo de Inteligência). Credenciais AWS temporárias expiradas são descartadas para o boto3 cair no role do nó.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict

_lock = threading.Lock()
_conn = None
STALE = ("390114", "390111", "Session no longer exists", "connection is closed", "251005",
         "Authentication token has expired")


def _secret() -> Dict[str, Any]:
    f = os.getenv("SNOWFLAKE_SECRET_FILE")
    if f and Path(f).exists():
        return json.loads(Path(f).read_text())
    import boto3

    sid = os.environ["SNOWFLAKE_SECRET_ID"]

    def get() -> str:
        client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "us-east-1"))
        return client.get_secret_value(SecretId=sid)["SecretString"]

    try:
        raw = get()
    except Exception as exc:
        if "ExpiredToken" not in str(exc):
            raise
        for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
            os.environ.pop(k, None)
        raw = get()
    return json.loads(raw)


def _connect():
    import snowflake.connector
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    sec = _secret()
    account = f"{sec['account']}.{sec['region']}" if sec.get("region") else sec["account"]
    cfg: Dict[str, Any] = {
        "user": sec["username"], "account": account, "role": sec.get("role"),
        "warehouse": sec.get("warehouse"),
        "database": os.getenv("SNOWFLAKE_DATABASE") or sec.get("database"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "EMBRAPII_DATASUS"),
        "paramstyle": "pyformat", "login_timeout": 20, "network_timeout": 60,
    }
    if sec.get("private_key"):
        pk = serialization.load_pem_private_key(sec["private_key"].encode(), password=None,
                                                backend=default_backend())
        cfg["private_key"] = pk.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                                              serialization.NoEncryption())
    else:
        cfg["password"] = sec["password"]
    return snowflake.connector.connect(**{k: v for k, v in cfg.items() if v})


def run(sql: str, params: Dict[str, Any]):
    """Executa e devolve lista de dicts. Reconecta uma vez se a sessão expirou."""
    global _conn

    def once():
        with _conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    with _lock:
        if _conn is None:
            _conn = _connect()
        try:
            return once()
        except Exception as exc:
            if not any(m in str(exc) for m in STALE):
                raise
            try:
                _conn.close()
            except Exception:
                pass
            _conn = _connect()
            return once()
```

O spec fala em pool de 4 conexões. Na prática, conexão única com lock mais o cache (Task 4) basta para uma demo. Se a latência incomodar na Task 15, troque por um pool.

- [ ] **Step 4: `backend/database.py`**

```python
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

ENGINES = ("postgres", "snowflake")


class DatabaseError(Exception):
    """Falha de banco, independente do engine."""


class Q:
    """SQL com uma versão por engine. `pg` é o texto original do Postgres."""

    def __init__(self, pg: str, sf: Optional[str] = None) -> None:
        self.pg = pg
        self.sf = sf

    def for_engine(self, engine: str) -> str:
        if engine == "postgres":
            return self.pg
        if self.sf is None:
            raise NotImplementedError("query sem versão Snowflake")
        return self.sf


def get_engine() -> str:
    engine = os.getenv("DB_ENGINE", "postgres").strip().lower()
    if engine not in ENGINES:
        raise RuntimeError(f"DB_ENGINE inválido: {engine!r} (use postgres ou snowflake)")
    return engine


_COMMENT = re.compile(r"(--[^\n]*\n)|(/\*.*?\*/)", re.S)


def _assert_read_only(sql: str) -> None:
    head = _COMMENT.sub("\n", sql).lstrip().split(None, 1)
    if not head or head[0].upper() not in ("SELECT", "WITH"):
        raise ValueError("Somente SELECT/WITH são permitidos.")


def get_connection():
    """Conexão Postgres somente leitura (usada também pelo /health/database)."""
    import psycopg
    from psycopg.rows import dict_row

    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise RuntimeError("Variáveis ausentes no arquivo .env: " + ", ".join(missing))
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"), dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), connect_timeout=5,
        row_factory=dict_row, options="-c default_transaction_read_only=on",
    )


def _run(engine: str, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    if engine == "postgres":
        import psycopg

        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    return list(cursor.fetchall())
        except psycopg.Error as exc:
            raise DatabaseError(str(exc)) from exc
    from backend import snowflake_conn

    try:
        return snowflake_conn.run(sql, params)
    except Exception as exc:
        raise DatabaseError(str(exc)) from exc


def _execute(query: Union[str, Q], params: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    q = query if isinstance(query, Q) else Q(pg=query)
    engine = get_engine()
    sql = q.for_engine(engine)
    _assert_read_only(sql)
    rows = _run(engine, sql, params or {})
    return [{str(k).lower(): v for k, v in row.items()} for row in rows]


def fetch_all(query: Union[str, Q], params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Executa um SELECT e retorna todas as linhas como dicionários."""
    return _execute(query, params)


def fetch_one(query: Union[str, Q], params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Executa um SELECT e retorna uma única linha como dicionário."""
    rows = _execute(query, params)
    return rows[0] if rows else None
```

- [ ] **Step 5: Routers capturam `DatabaseError`**

Em cada `backend/api/*.py`, troque `except psycopg.Error as exc:` por `except DatabaseError as exc:`, importe `from backend.database import DatabaseError, Q, fetch_all, fetch_one`, remova `import psycopg` e troque o texto de `_database_error` para `f"Erro ao consultar o banco: {exc}"`. `except (psycopg.Error, RuntimeError)` em outros pontos vira `except (DatabaseError, RuntimeError)`.

Run: `grep -n "psycopg" backend/api/*.py`
Expected: nenhuma linha.

- [ ] **Step 6: Rodar os testes**

Run: `.venv/bin/pytest backend/tests -q`
Expected: `10 passed`.

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat(dashboard): camada de engine postgres|snowflake com guarda SELECT-only"
```

---

### Task 4: Cache TTL

**Files:** Create: `backend/cache.py`, `backend/tests/test_cache.py`; Modify: `backend/database.py` (`_execute`)

- [ ] **Step 1: Teste que falha**

`backend/tests/test_cache.py`:

```python
from backend.cache import TTLCache


def test_cache_hit_e_expira():
    now = [0.0]
    c = TTLCache(ttl=10, clock=lambda: now[0])
    calls = []

    def load():
        calls.append(1)
        return [1]

    assert c.get_or_load(("k",), load) == [1]
    assert c.get_or_load(("k",), load) == [1]
    assert len(calls) == 1
    now[0] = 11
    c.get_or_load(("k",), load)
    assert len(calls) == 2


def test_ttl_zero_desliga():
    c = TTLCache(ttl=0)
    calls = []
    c.get_or_load(("k",), lambda: calls.append(1))
    c.get_or_load(("k",), lambda: calls.append(1))
    assert len(calls) == 2
```

- [ ] **Step 2: Ver falhar**

Run: `.venv/bin/pytest backend/tests/test_cache.py -q`
Expected: FAIL (`ModuleNotFoundError: backend.cache`).

- [ ] **Step 3: Implementar**

`backend/cache.py`:

```python
from __future__ import annotations

import os
import threading
import time
from typing import Any, Callable, Dict, Hashable, Tuple


class TTLCache:
    def __init__(self, ttl: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.ttl = ttl
        self.clock = clock
        self._data: Dict[Hashable, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get_or_load(self, key: Hashable, load: Callable[[], Any]) -> Any:
        if self.ttl <= 0:
            return load()
        with self._lock:
            hit = self._data.get(key)
            if hit and self.clock() - hit[0] < self.ttl:
                return hit[1]
        value = load()
        with self._lock:
            self._data[key] = (self.clock(), value)
        return value


query_cache = TTLCache(ttl=float(os.getenv("QUERY_CACHE_TTL_SECONDS", "3600")))
```

Em `database.py`, `_execute` passa a usar o cache. A chave inclui engine, SQL e parâmetros ordenados; datas viram `str`.

```python
def _execute(query: Union[str, Q], params: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from backend.cache import query_cache

    q = query if isinstance(query, Q) else Q(pg=query)
    engine = get_engine()
    sql = q.for_engine(engine)
    _assert_read_only(sql)
    p = params or {}
    key = (engine, sql, tuple(sorted((k, str(v)) for k, v in p.items())))

    def load() -> List[Dict[str, Any]]:
        rows = _run(engine, sql, p)
        return [{str(k).lower(): v for k, v in row.items()} for row in rows]

    return query_cache.get_or_load(key, load)
```

- [ ] **Step 4: Rodar tudo**

Run: `QUERY_CACHE_TTL_SECONDS=0 .venv/bin/pytest backend/tests -q`
Expected: `12 passed`. Com TTL 0 os testes de `database` não se contaminam via cache.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(dashboard): cache TTL das consultas"
```

---

### Task 5: FastAPI serve o front sob qualquer prefixo

**Files:** Create: `backend/static.py`, `backend/tests/test_static.py`; Modify: `backend/main.py`

Regras:
- `APP_BASE_PATH` (ex.: `/pbp-service-dataapp-…_8000`, sem barra final; vazio localmente).
- `FRONTEND_DIST` (default `<Dashboard>/frontend/dist`). Se o diretório não existir, nada é montado e a API funciona igual.
- `GET /assets/*`, `/maps/*`, `/logos/*` e arquivos com extensão viram arquivo estático. Qualquer outro GET que não seja `/api/*` nem `/health*` recebe o `index.html` com `<base href="{APP_BASE_PATH}/">` e `<script>window.__APP_BASE__="{APP_BASE_PATH}"</script>` injetados logo após `<head>`.
- Com `preserve_base_path: True`, o Orchest entrega o path **com** o prefixo. Um middleware remove `APP_BASE_PATH` do início do path antes do roteamento.

- [ ] **Step 1: Testes que falham**

`backend/tests/test_static.py`:

```python
import importlib

from fastapi.testclient import TestClient


def make_client(tmp_path, monkeypatch, base=""):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html><head><title>x</title></head><body></body></html>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    monkeypatch.setenv("APP_BASE_PATH", base)
    import backend.main as main

    importlib.reload(main)
    return TestClient(main.app)


def test_spa_fallback_injeta_base(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="/pbp-x_8000")
    r = c.get("/pbp-x_8000/leitos")
    assert r.status_code == 200
    assert '<base href="/pbp-x_8000/">' in r.text
    assert 'window.__APP_BASE__="/pbp-x_8000"' in r.text


def test_asset_com_prefixo(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="/pbp-x_8000")
    r = c.get("/pbp-x_8000/assets/app.js")
    assert r.status_code == 200 and "console.log" in r.text


def test_health_com_e_sem_prefixo(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="/pbp-x_8000")
    assert c.get("/pbp-x_8000/health").json() == {"status": "ok"}
    assert c.get("/health").json() == {"status": "ok"}


def test_local_sem_prefixo(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="")
    r = c.get("/compras")
    assert '<base href="/">' in r.text
```

- [ ] **Step 2: Ver falhar**

Run: `.venv/bin/pytest backend/tests/test_static.py -q`
Expected: FAIL (404 ou `base href` ausente).

- [ ] **Step 3: `backend/static.py`**

```python
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, Response

DEFAULT_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"


def base_path() -> str:
    return os.getenv("APP_BASE_PATH", "").rstrip("/")


def install(app: FastAPI) -> None:
    dist = Path(os.getenv("FRONTEND_DIST", str(DEFAULT_DIST)))
    base = base_path()

    @app.middleware("http")
    async def strip_base(request: Request, call_next):
        path = request.scope["path"]
        if base and (path == base or path.startswith(base + "/")):
            request.scope["path"] = path[len(base):] or "/"
        return await call_next(request)

    if not (dist / "index.html").exists():
        return
    index = (dist / "index.html").read_text(encoding="utf-8")
    inject = f'<base href="{base}/"><script>window.__APP_BASE__="{base}"</script>'
    index = index.replace("<head>", "<head>" + inject, 1)

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> Response:
        if full_path.startswith(("api/", "health")):
            return Response(status_code=404)
        candidate = (dist / full_path).resolve()
        if full_path and candidate.is_file() and dist.resolve() in candidate.parents:
            return FileResponse(candidate)
        return HTMLResponse(index, headers={"Cache-Control": "no-cache"})
```

- [ ] **Step 4: Ligar no `main.py`**

Ao final de `backend/main.py`, depois dos `include_router` e das rotas `/health`:

```python
from backend import static  # noqa: E402

static.install(app)
```

O catch-all precisa ser registrado **depois** de todas as rotas da API. Em `/health/database`, devolva também o engine:

```python
@app.get("/health/database")
def database_health():
    """Testa a comunicação da API com o banco do engine ativo."""
    engine = get_engine()
    try:
        row = fetch_one(Q(pg="SELECT 1 AS result", sf="SELECT 1 AS result"))
        return {"status": "ok", "engine": engine, "result": row["result"] if row else None}
    except (DatabaseError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=f"Banco indisponível ({engine}): {exc}") from exc
```

Importe `from backend.database import DatabaseError, Q, fetch_one, get_engine`, remova o `import psycopg` e o `get_connection` do `main.py` e amplie o CORS: `allow_methods=["GET"]` continua.

- [ ] **Step 5: Rodar**

Run: `QUERY_CACHE_TTL_SECONDS=0 .venv/bin/pytest backend/tests -q`
Expected: `16 passed`.

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat(dashboard): FastAPI serve o front sob o prefixo do Orchest"
```

---

### Task 6: Front roda sob prefixo (`base.ts`, Vite, router, GeoJSON)

**Files:** Create: `frontend/src/lib/base.ts`; Modify: `frontend/vite.config.ts`, `frontend/src/main.tsx`, `frontend/src/components/MapaBrasil.tsx:109-111`

- [ ] **Step 1: `frontend/src/lib/base.ts`**

```ts
declare global {
  interface Window {
    __APP_BASE__?: string;
  }
}

/** Prefixo do app ("" local, "/pbp-service-…_8000" no Orchest), injetado pelo FastAPI. */
export const APP_BASE: string = (window.__APP_BASE__ ?? "").replace(/\/$/, "");

const API_ORIGIN: string = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

/** URL de um endpoint da API: apiUrl("/api/compras/kpis"). */
export function apiUrl(path: string): string {
  return `${API_ORIGIN || APP_BASE}${path}`;
}

/** URL de um arquivo de public/: assetUrl("maps/brasil-ufs.geojson"). */
export function assetUrl(path: string): string {
  return `${APP_BASE}/${path.replace(/^\//, "")}`;
}
```

- [ ] **Step 2: Vite, router e mapa**

`frontend/vite.config.ts`: adicione `base: "./",` no objeto de `defineConfig`.

`frontend/src/main.tsx`: `import { APP_BASE } from "./lib/base";` e `<BrowserRouter basename={APP_BASE || "/"}>`.

`frontend/src/components/MapaBrasil.tsx`: `import { assetUrl } from "../lib/base";` e troque `fetch("/maps/brasil-ufs.geojson")` por `fetch(assetUrl("maps/brasil-ufs.geojson"))`.

Run: `grep -rn '"/maps\|"/logos\|src="/' frontend/src frontend/index.html`
Expected: nenhuma ocorrência restante com caminho absoluto. Converta as que sobrarem com `assetUrl`; no `index.html`, remova a barra inicial (`href="favicon.svg"`).

- [ ] **Step 3: Commit (o build só passa na Task 7)**

```bash
git add frontend/
git commit -m "feat(dashboard): front resolve API e assets pelo prefixo em runtime"
```

---

### Task 7: Reconstruir `lib/api.ts` e `lib/fornecedoresApi.ts`

**Files:** Create: `frontend/src/lib/http.ts`, `frontend/src/lib/api.ts`, `frontend/src/lib/fornecedoresApi.ts`

Os dois arquivos foram perdidos pelo `.gitignore`. Eles são reconstruídos a partir de três fontes: (a) o que as páginas importam, (b) como cada função é chamada e (c) o JSON real de cada endpoint. O `tsc` é o juiz: sem erro de tipo nas páginas, a reconstrução está compatível.

- [ ] **Step 1: `frontend/src/lib/http.ts`**

```ts
import { apiUrl } from "./base";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

type Param = string | number | boolean | null | undefined;

export async function request<T>(path: string, params: Record<string, Param> = {}): Promise<T> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  }
  const query = qs.toString();
  const response = await fetch(apiUrl(path) + (query ? `?${query}` : ""));
  if (!response.ok) {
    let detail = `Erro ${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* corpo não-JSON */
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}
```

- [ ] **Step 2: Inventário dos imports**

Run:
```bash
cd frontend && for f in src/pages/*.tsx src/components/*.tsx; do
  awk '/^import \{$/{b=""} {b=b $0 "\n"} /from "\.\.\/lib\/(api|fornecedoresApi)";/{print FILENAME; print b}' "$f"; done
```
Expected: os blocos de import de `Compras`, `Medicamentos`, `Mapa`, `Leitos` (de `../lib/api`) e `Fornecedores` (de `../lib/fornecedoresApi`). A lista completa de nomes (funções e `type`) é o contrato a cumprir.

- [ ] **Step 3: Mapear função → endpoint**

Siga esta tabela. A assinatura de cada função é a que as páginas usam (confirme cada uma lendo a chamada, com `grep -n "<nome>(" -A6 src/pages/*.tsx`).

| Função | Arquivo | Endpoint | Parâmetros de query |
|---|---|---|---|
| `buscarMedicamentos(q, limite?)` | api | `/api/medicamentos/busca` | `q`, `limite` |
| `listarProdutos(catmatId)` | api | `/api/medicamentos/{catmat_id}/produtos` | — |
| `buscarResumoMedicamento(catmatId)` | api | `/api/medicamentos/{catmat_id}/resumo` | — |
| `buscarLotesVencendo(catmatId, dias)` | api | `/api/medicamentos/{catmat_id}/lotes-vencendo` | `dias` |
| `buscarEstoquePorUf(catmatId)` | api | `/api/medicamentos/{catmat_id}/estoque-por-uf` | — |
| `buscarEvolucaoPreco(catmatId)` | api | `/api/medicamentos/{catmat_id}/compras/evolucao-preco` | — |
| `buscarFornecedores(catmatId, limite)` | api | `/api/medicamentos/{catmat_id}/compras/fornecedores` | `limite` |
| `buscarFabricantes(catmatId, limite)` | api | `/api/medicamentos/{catmat_id}/compras/fabricantes` | `limite` |
| `buscarHistoricoCompras(catmatId, limite, offset)` | api | `/api/medicamentos/{catmat_id}/compras` | `limite`, `offset` |
| `buscarKpisCompras(filtros)` | api | `/api/compras/kpis` | `FiltrosCompras` → `data_inicio`, `data_fim`, `catmat_id`, `tipo_compra` |
| `buscarComprasPorMes(filtros)` | api | `/api/compras/por-mes` | idem |
| `buscarRankingFornecedores(filtros, limite)` | api | `/api/compras/fornecedores` | idem + `limite` |
| `buscarRankingFabricantes(filtros, limite)` | api | `/api/compras/fabricantes` | idem + `limite` |
| `buscarComprasPorModalidade(filtros)` | api | `/api/compras/modalidades` | idem |
| `buscarComprasPorTipo(filtros)` | api | `/api/compras/tipos` | idem |
| `buscarComprasRecentes(filtros, limite)` | api | `/api/compras/recentes` | idem + `limite` |
| `buscarOpcoesLeitos()` | api | `/api/leitos/opcoes` | — |
| `buscarPainelLeitos(filtros, dataInicio, dataFim)` | api | `/api/leitos/painel` | `FiltrosLeitos` + `data_inicio`, `data_fim` |
| `buscarLeitosPorUf({ modo, uf })` | api | `/api/leitos/por-uf` | `modo`, `uf` |
| `buscarMapaFornecedoresPorUf(dataInicio, dataFim)` | fornecedoresApi | `/api/fornecedores/mapa-por-uf` | `data_inicio`, `data_fim` |
| `buscarRankingFornecedores(dataInicio, dataFim, uf?, limite)` | fornecedoresApi | `/api/fornecedores/ranking` | `data_inicio`, `data_fim`, `uf`, `limite` |

Para os parâmetros do `/api/leitos/painel`, leia a assinatura em `backend/api/leitos.py:1166` e os campos de `FiltrosLeitos` usados em `Leitos.tsx`. Os nomes da query são os nomes dos parâmetros Python, e as chaves do objeto TS mapeiam 1:1 (camelCase → snake_case onde houver).

- [ ] **Step 4: Tipos a partir do JSON real**

Antes, execute a Task 8, Steps 1 e 2 (túnel e `.env`). Depois suba o backend contra o Postgres e colete uma resposta por endpoint:

```bash
DB_ENGINE=postgres .venv/bin/uvicorn backend.main:app --port 8000 &
curl -s "localhost:8000/api/medicamentos/busca?q=dipirona&limite=3" | python -m json.tool | head -40
```

Para cada endpoint, escreva a interface TS com os campos do JSON: `number` para numéricos (o FastAPI serializa `Decimal` como string se não houver conversão, então confira: se vier `"123.45"`, tipar `number | string` e converter com `Number()` na função), `string` para datas, e `| null` quando o campo pode vir nulo. Os nomes dos tipos são exatamente os importados pelas páginas (Step 2). Quando a página usa um campo que o JSON não tem, o erro está no mapeamento de endpoint: volte ao Step 3.

Forma de cada função (exemplo real):

```ts
export interface FiltrosCompras {
  dataInicio: string;
  dataFim: string;
  catmatId?: number | null;
  tipoCompra?: string;
}

function paramsCompras(f: FiltrosCompras) {
  return { data_inicio: f.dataInicio, data_fim: f.dataFim, catmat_id: f.catmatId, tipo_compra: f.tipoCompra };
}

export function buscarKpisCompras(filtros: FiltrosCompras): Promise<KpisCompras> {
  return request<KpisCompras>("/api/compras/kpis", paramsCompras(filtros));
}
```

Os campos de `FiltrosCompras` precisam bater com o que `Compras.tsx` monta: leia a construção de `filtros` perto da linha 700 e ajuste os nomes.

- [ ] **Step 5: Type-check e build**

Run: `cd frontend && npm ci --registry=https://registry.npmjs.org/ && npx tsc -b --noEmit && npm run build`
Expected: zero erros; `dist/index.html` gerado com assets relativos (`./assets/...`).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/
git commit -m "feat(dashboard): reconstroi lib/api.ts e lib/fornecedoresApi.ts (perdidos pelo gitignore)"
```

---

### Task 8: Túnel, `.env` e smoke local contra o Postgres

**Files:** Create: `scripts/tunnel.sh`, `.env.example` (atualizar); Local: `.env` (não versionado)

- [ ] **Step 1: `scripts/tunnel.sh`**

```bash
#!/usr/bin/env bash
# Túnel para o Postgres da UFMG: localhost:5433 -> 150.164.2.13:5432 via bastion.
# Requer SSH_USER, SSH_HOST e SSH_PASSWORD no Dashboard/.env. Uso: scripts/tunnel.sh (Ctrl+C encerra).
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
export SSHPW="$SSH_PASSWORD"
exec expect -c '
  set timeout 30
  log_user 0
  spawn ssh -N -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
    -L 5433:150.164.2.13:5432 $env(SSH_USER)@$env(SSH_HOST)
  expect -re "(?i)password:" { send "$env(SSHPW)\r" }
  expect { -re "(?i)denied|password:" { puts "AUTH FAILED"; exit 2 } timeout { puts "TUNNEL UP on :5433" } }
  set timeout -1
  expect eof'
```

Run: `chmod +x scripts/tunnel.sh`

- [ ] **Step 2: `.env` local (não commitar)**

Copie do `.env.example` e preencha: `SSH_HOST=150.164.2.44`, `SSH_USER=lbduser`, `SSH_PASSWORD=` (a do `dados_datasus/README.md`), `DB_HOST=127.0.0.1`, `DB_PORT=5433`, `DB_NAME=datalake_db2`, `DB_USER=datalake_user`, `DB_PASSWORD=` (a do `dados_datasus/datalake.py`), `SNOWFLAKE_SECRET_FILE=/Users/allansene/Repos/dadosfera/kine-gest-ddf-oic/apps/oic-visitors/.secrets/snow-dadosferademo.json`, `SNOWFLAKE_SCHEMA=EMBRAPII_DATASUS`. No `.env.example`, acrescente as chaves com valor vazio.

- [ ] **Step 3: Smoke contra Postgres**

```bash
scripts/tunnel.sh &   # "TUNNEL UP on :5433"
(cd frontend && npm run build)
DB_ENGINE=postgres .venv/bin/uvicorn backend.main:app --port 8000
curl -s localhost:8000/health/database
```

Expected: `{"status":"ok","engine":"postgres","result":1}`, e `http://localhost:8000/` abre o dashboard com dados nas 6 páginas.

- [ ] **Step 4: Commit**

```bash
git add scripts/tunnel.sh .env.example
git commit -m "chore(dashboard): tunel SSH e env de exemplo"
```

---

### Task 9: Smoke Playwright das 6 páginas

**Files:** Create: `frontend/playwright.config.ts`, `frontend/e2e/smoke.spec.ts`; Modify: `frontend/package.json` (devDependency `@playwright/test`, script `"e2e": "playwright test"`)

- [ ] **Step 1: Descobrir as rotas**

Run: `grep -n "path=" frontend/src/App.tsx`
Expected: as rotas das páginas Home, Medicamentos, Compras, Leitos, Mapa e Fornecedores. Use exatamente esses paths no teste.

- [ ] **Step 2: Config e teste**

`frontend/playwright.config.ts`:

```ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  timeout: 90_000,
  use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8000/" },
});
```

`frontend/e2e/smoke.spec.ts` (troque `ROTAS` pelos paths do Step 1, sem barra inicial):

```ts
import { expect, test } from "@playwright/test";

const ROTAS = ["", "medicamentos", "compras", "leitos", "mapa", "fornecedores"];

for (const rota of ROTAS) {
  test(`página /${rota} carrega sem erro`, async ({ page }) => {
    const erros: string[] = [];
    page.on("console", (m) => m.type() === "error" && erros.push(m.text()));
    page.on("response", (r) => r.url().includes("/api/") && r.status() >= 400 && erros.push(`${r.status()} ${r.url()}`));
    await page.goto(rota);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).not.toContainText("Não foi possível");
    expect(erros).toEqual([]);
  });
}
```

O `baseURL` termina em `/` e as rotas não têm `/` inicial, então o Playwright resolve dentro do prefixo do Orchest.

- [ ] **Step 3: Rodar contra o backend local (Task 8)**

Run: `cd frontend && npm i -D @playwright/test --registry=https://registry.npmjs.org/ && npx playwright install chromium && npx playwright test`
Expected: `6 passed`. Se uma página falhar por texto de erro próprio dela, ajuste a asserção para o texto real de erro que ela exibe (leia o `catch` da página).

- [ ] **Step 4: Commit**

```bash
git add frontend/playwright.config.ts frontend/e2e frontend/package.json frontend/package-lock.json
git commit -m "test(dashboard): smoke Playwright das 6 paginas"
```

---

### Task 10: Sync Postgres → Snowflake

**Files:** Create: `scripts/tables.txt`, `scripts/sync_snowflake.py`, `backend/tests/test_sync.py`

- [ ] **Step 1: `scripts/tables.txt`**

```text
catmat
cnpj_enriquecido
endereco
fabricante
fornecedor
instituicao
instituicao_estoca_produto
leitos
mantenedora
mantenedora_compra_produto
municipio
produto
regiao_de_saude
macrorregiao_de_saude
unidade_federativa
regiao_do_brasil
v_endereco_completo
```

`regiao_de_saude`, `macrorregiao_de_saude`, `unidade_federativa` e `regiao_do_brasil` entram porque a view `v_endereco_completo` depende delas. A view vira tabela no Snowflake.

- [ ] **Step 2: Teste que falha (referências dos routers ⊆ tables.txt ∪ CTEs)**

`backend/tests/test_sync.py`:

```python
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def referenced_relations():
    text = "\n".join(p.read_text() for p in (ROOT / "backend" / "api").glob("*.py"))
    sql_refs = set(re.findall(r"(?i)\b(?:from|join)\s+([a-z_][a-z0-9_]*)\s", text))
    ctes = set(re.findall(r"(?i)\b([a-z_][a-z0-9_]*)\s+as\s+(?:materialized\s+)?\(", text))
    py_imports = {"backend", "datetime", "fastapi", "functools", "time", "typing", "exc", "lateral"}
    return {r.lower() for r in sql_refs} - {c.lower() for c in ctes} - py_imports


def test_tables_txt_cobre_routers():
    tables = set((ROOT / "scripts" / "tables.txt").read_text().split())
    faltando = referenced_relations() - tables
    assert not faltando, f"routers citam relações fora de scripts/tables.txt: {sorted(faltando)}"
```

Run: `.venv/bin/pytest backend/tests/test_sync.py -q`
Expected: PASS se o Step 1 estiver certo. Se falhar, a mensagem lista o que falta: adicione a tabela real ou o nome ao `py_imports`, se for import Python.

- [ ] **Step 3: `scripts/sync_snowflake.py`**

```python
#!/usr/bin/env python3
"""Copia as tabelas do Dashboard do Postgres da UFMG (datalake_db2, via túnel) para o Snowflake EMBRAPII_DATASUS.

Uso: scripts/tunnel.sh &  ;  .venv/bin/python scripts/sync_snowflake.py [--only t1,t2] [--resume]
Cada tabela: COPY (SELECT) TO STDOUT em CSV no servidor → parquet local → PUT no stage → CREATE OR REPLACE
TABLE ... USING TEMPLATE → COPY INTO → confere contagem. Relatório em scripts/sync_report.json.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import tempfile
from pathlib import Path

import pyarrow.csv as pacsv
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend import snowflake_conn  # noqa: E402
from backend.database import get_connection  # noqa: E402

REPORT = ROOT / "scripts" / "sync_report.json"
MAX_BYTES = 5 * 1024**3
STOCK = "instituicao_estoca_produto"
STOCK_SQL = f"""
    SELECT DISTINCT ON (instituicao_id, produto_id) *
    FROM {STOCK}
    ORDER BY instituicao_id, produto_id,
             data_de_posicao_no_estoque DESC NULLS LAST,
             instituicao_estoca_produto_id DESC
"""


def source_sql(table: str) -> str:
    return STOCK_SQL if table == STOCK else f"SELECT * FROM {table}"


def pg_count(cur, table: str) -> int:
    cur.execute(f"SELECT count(*) AS n FROM ({source_sql(table)}) s")
    return cur.fetchone()["n"]


def sizes(cur, tables):
    cur.execute(
        "SELECT relname, pg_total_relation_size(oid) AS b FROM pg_class WHERE relname = ANY(%(t)s)",
        {"t": list(tables)},
    )
    return {r["relname"]: r["b"] for r in cur.fetchall()}


def export_parquet(pg, table: str, out: Path) -> None:
    buf = io.BytesIO()
    with pg.cursor().copy(f"COPY ({source_sql(table)}) TO STDOUT WITH CSV HEADER") as cp:
        for chunk in cp:
            buf.write(chunk)
    buf.seek(0)
    tbl = pacsv.read_csv(buf, convert_options=pacsv.ConvertOptions(strings_can_be_null=True))
    tbl = tbl.rename_columns([c.upper() for c in tbl.column_names])
    pq.write_table(tbl, out)


def load_snowflake(table: str, parquet: Path) -> int:
    t = table.upper()
    run = snowflake_conn.run
    run("CREATE STAGE IF NOT EXISTS EMBRAPII_SYNC FILE_FORMAT = (TYPE = PARQUET)", {})
    run(f"PUT file://{parquet} @EMBRAPII_SYNC/{t}/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE", {})
    run(
        f"""CREATE OR REPLACE TABLE {t} USING TEMPLATE (
              SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*)) FROM TABLE(INFER_SCHEMA(
                LOCATION => '@EMBRAPII_SYNC/{t}/', FILE_FORMAT => 'EMBRAPII_PARQUET')))""",
        {},
    )
    run(f"COPY INTO {t} FROM @EMBRAPII_SYNC/{t}/ FILE_FORMAT = (FORMAT_NAME = 'EMBRAPII_PARQUET') "
        "MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE PURGE = TRUE", {})
    return run(f"SELECT COUNT(*) AS N FROM {t}", {})[0]["N"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--resume", action="store_true", help="pula tabelas já OK no relatório")
    args = ap.parse_args()
    tables = (ROOT / "scripts" / "tables.txt").read_text().split()
    if args.only:
        tables = [t for t in tables if t in args.only.split(",")]
    report = json.loads(REPORT.read_text()) if REPORT.exists() else {}

    snowflake_conn.run("CREATE SCHEMA IF NOT EXISTS EMBRAPII_DATASUS", {})
    snowflake_conn.run("CREATE FILE FORMAT IF NOT EXISTS EMBRAPII_PARQUET TYPE = PARQUET", {})

    with get_connection() as pg:
        with pg.cursor() as cur:
            sz = sizes(cur, tables)
        estimate = sum(b for t, b in sz.items() if t != STOCK)
        if estimate > MAX_BYTES:
            sys.exit(f"volume estimado {estimate / 1024**3:.1f} GB > 5 GB (sem contar o recorte do estoque)")
        for table in tables:
            if args.resume and report.get(table, {}).get("ok"):
                print(f"= {table} (já OK)")
                continue
            with pg.cursor() as cur:
                src = pg_count(cur, table)
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / f"{table}.parquet"
                export_parquet(pg, table, out)
                dst = load_snowflake(table, out)
            report[table] = {"source_rows": src, "snowflake_rows": dst, "ok": src == dst}
            REPORT.write_text(json.dumps(report, indent=2))
            print(f"{'OK' if src == dst else 'DIVERGE'} {table}: pg={src} sf={dst}")

    bad = [t for t, r in report.items() if not r["ok"]]
    if bad:
        sys.exit(f"contagens divergentes: {bad}")
    print("sync completo")


if __name__ == "__main__":
    main()
```

Adicione `scripts/sync_report.json` ao `Dashboard/.gitignore`.

O `COPY ... CSV` com `pyarrow.csv` perde o tipo de algumas colunas (datas viram string se o parser não reconhecer, e `numeric` vira `double`). Depois da primeira carga, confira os tipos com `DESCRIBE TABLE` no Snowflake para `mantenedora_compra_produto`, `leitos` e `instituicao_estoca_produto`. Se `data_*` vier como `VARCHAR`, passe `column_types` explícitos ao `pacsv.ConvertOptions` para essas colunas (`pa.date32()` ou `pa.timestamp("us", tz="UTC")`) e recarregue com `--only`. A paridade (Task 11) acusa qualquer diferença de tipo que mude resultado.

- [ ] **Step 4: Rodar a carga**

```bash
scripts/tunnel.sh &
.venv/bin/python scripts/sync_snowflake.py --only municipio,fornecedor   # teste pequeno
.venv/bin/python scripts/sync_snowflake.py --resume
```

Expected: uma linha `OK <tabela>: pg=N sf=N` por tabela e `sync completo`. `instituicao_estoca_produto` deve dar ~3,3 M linhas. Esse `DISTINCT ON` roda no servidor e pode levar alguns minutos. Se o túnel cair, reabra e rode com `--resume`.

- [ ] **Step 5: Commit**

```bash
git add scripts/tables.txt scripts/sync_snowflake.py backend/tests/test_sync.py .gitignore
git commit -m "feat(dashboard): sync Postgres UFMG -> Snowflake EMBRAPII_DATASUS"
```

---

### Task 11: Harness de paridade

**Files:** Create: `tests/parity/cases.yaml`, `tests/parity/test_parity.py`, `tests/parity/conftest.py`

Os IDs dos casos são `<router>-<n>` (ex.: `compras-4`), então `-k compras` seleciona só `/api/compras/*`, sem os casos `medicamentos/.../compras`. O harness chama cada endpoint duas vezes, via TestClient, trocando `DB_ENGINE`, e compara. O cache fica desligado.

- [ ] **Step 1: `tests/parity/cases.yaml`**

Um caso por endpoint, mais um "sem filtro" onde houver filtro opcional. Use os valores abaixo e troque `CATMAT` pelo ID que sai do primeiro resultado de `/api/medicamentos/busca?q=dipirona`, conferido contra o Postgres.

```yaml
catmat: CATMAT
periodo: {data_inicio: "2024-01-01", data_fim: "2024-12-31"}
cases:
  - /api/fornecedores/mapa-por-uf?data_inicio={data_inicio}&data_fim={data_fim}
  - /api/fornecedores/ranking?data_inicio={data_inicio}&data_fim={data_fim}&limite=50
  - /api/fornecedores/ranking?data_inicio={data_inicio}&data_fim={data_fim}&uf=MG&limite=50
  - /api/fornecedores/top-por-uf?data_inicio={data_inicio}&data_fim={data_fim}
  - /api/compras/kpis?data_inicio={data_inicio}&data_fim={data_fim}
  - /api/compras/kpis?data_inicio={data_inicio}&data_fim={data_fim}&catmat_id={catmat}
  - /api/compras/por-mes?data_inicio={data_inicio}&data_fim={data_fim}
  - /api/compras/fornecedores?data_inicio={data_inicio}&data_fim={data_fim}&limite=15
  - /api/compras/fabricantes?data_inicio={data_inicio}&data_fim={data_fim}&limite=15
  - /api/compras/modalidades?data_inicio={data_inicio}&data_fim={data_fim}
  - /api/compras/tipos?data_inicio={data_inicio}&data_fim={data_fim}
  - /api/compras/recentes?data_inicio={data_inicio}&data_fim={data_fim}&limite=200
  - /api/medicamentos/busca?q=dipirona&limite=50
  - /api/medicamentos/{catmat}/produtos
  - /api/medicamentos/{catmat}/resumo
  - /api/medicamentos/{catmat}/lotes-vencendo?dias=90
  - /api/medicamentos/{catmat}/estoque-por-uf
  - /api/medicamentos/{catmat}/compras/evolucao-preco
  - /api/medicamentos/{catmat}/compras/fornecedores?limite=15
  - /api/medicamentos/{catmat}/compras/fabricantes?limite=15
  - /api/medicamentos/{catmat}/compras?limite=200&offset=0
  - /api/leitos/intervalo
  - /api/leitos/ufs
  - /api/leitos/kpis
  - /api/leitos/kpis?uf=MG
  - /api/leitos/por-uf
  - /api/leitos/tipos-uti
  - /api/leitos/evolucao?data_inicio={data_inicio}&data_fim={data_fim}
  - /api/leitos/instituicoes?limite=100
  - /api/leitos/opcoes
  - /api/leitos/painel?data_inicio={data_inicio}&data_fim={data_fim}
```

Confira os parâmetros obrigatórios de cada endpoint de `leitos` na assinatura (`leitos.py:138-1170`) e acrescente o que faltar. Se `/api/medicamentos/{catmat}/lotes-vencendo` depender de `CURRENT_DATE`, o resultado muda com o dia e a paridade roda os dois engines no mesmo minuto, então não há problema.

- [ ] **Step 2: `tests/parity/conftest.py` e `test_parity.py`**

`tests/parity/conftest.py`:

```python
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ["QUERY_CACHE_TTL_SECONDS"] = "0"
```

`tests/parity/test_parity.py`:

```python
from __future__ import annotations

import json
import math
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

HERE = Path(__file__).parent
CFG = yaml.safe_load((HERE / "cases.yaml").read_text())
CASES = [c.format(catmat=CFG["catmat"], **CFG["periodo"]) for c in CFG["cases"]]
REPORT = HERE / "report.md"
RESULTS: dict = {}


def norm(v):
    if isinstance(v, dict):
        return {k.lower(): norm(x) for k, x in sorted(v.items())}
    if isinstance(v, list):
        return sorted((norm(x) for x in v), key=lambda x: json.dumps(x, sort_keys=True, default=str))
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
        return round(float(v), 6)
    if isinstance(v, str):
        try:
            return round(float(v), 6)
        except ValueError:
            return v.replace("T00:00:00", "").replace("+00:00", "")
    return v


def call(monkeypatch, engine: str, path: str):
    monkeypatch.setenv("DB_ENGINE", engine)
    from backend.main import app

    r = TestClient(app).get(path)
    return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text)


def same(a, b) -> bool:
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, abs_tol=1e-6, rel_tol=1e-9)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


@pytest.mark.parametrize("path", CASES, ids=[f"{c.split('/')[2]}-{i}" for i, c in enumerate(CASES)])
def test_paridade(monkeypatch, path):
    s_pg, pg = call(monkeypatch, "postgres", path)
    s_sf, sf = call(monkeypatch, "snowflake", path)
    ok = s_pg == s_sf == 200 and same(norm(pg), norm(sf))
    RESULTS[path] = (ok, s_pg, s_sf)
    assert s_pg == 200, f"postgres {s_pg}: {pg}"
    assert s_sf == 200, f"snowflake {s_sf}: {sf}"
    assert ok, f"divergência em {path}"


def teardown_module(module):
    linhas = ["# Paridade Postgres × Snowflake", "", "| Endpoint | PG | SF | OK |", "|---|---|---|---|"]
    for p, (ok, a, b) in RESULTS.items():
        linhas.append(f"| `{p}` | {a} | {b} | {'✅' if ok else '❌'} |")
    total = sum(1 for ok, *_ in RESULTS.values() if ok)
    linhas += ["", f"**{total}/{len(RESULTS)} iguais**"]
    REPORT.write_text("\n".join(linhas) + "\n")
```

Quando as listas não têm ordem garantida, `norm` ordena tudo. Isso esconde diferença de `ORDER BY` entre engines, o que é aceito aqui: ordem de exibição é responsabilidade da query e o dashboard reordena nas tabelas. Endpoints de ranking (`ranking`, `fornecedores`, `fabricantes` com `LIMIT`) podem divergir em empates no último lugar. Nesses casos, adicione desempate determinístico (`, <nome> ASC`) no `ORDER BY` das **duas** versões e registre no commit.

- [ ] **Step 3: Rodar (esperado: tudo vermelho no Snowflake)**

Run: `.venv/bin/pytest tests/parity -q -x --maxfail=50 2>&1 | tail -5`
Expected: falhas com `NotImplementedError: query sem versão Snowflake` (status 500). É o ponto de partida para as Tasks 12-15.

- [ ] **Step 4: Commit**

```bash
git add tests/parity/cases.yaml tests/parity/test_parity.py tests/parity/conftest.py
git commit -m "test(dashboard): harness de paridade Postgres x Snowflake"
```

---

### Regras de porte (valem para as Tasks 12-15)

Cada query do router vira `Q(pg="""<texto original, sem mudar um byte>""", sf="""<porte>""")`, passada a `fetch_all`/`fetch_one`. Fragmentos dinâmicos (`_montar_filtros`, `filtro_uf` etc.) recebem `engine: str` e devolvem o texto do engine. O router obtém o engine com `get_engine()` no início do handler.

| Postgres | Snowflake |
|---|---|
| `SUM(x) FILTER (WHERE c)` | `SUM(IFF(c, x, NULL))` |
| `COUNT(*) FILTER (WHERE c)` | `COUNT_IF(c)` |
| `BTRIM(s)` | `TRIM(s)` |
| `x::date`, `x::numeric` | igual (`::date`, `::number`) |
| `DATE_TRUNC('month', d)::date` | igual |
| `d + (%(dias)s * INTERVAL '1 day')` | `DATEADD(day, %(dias)s, d)` |
| `CURRENT_DATE` | igual |
| `SELECT DISTINCT ON (a) ... ORDER BY a, b DESC` | `SELECT ... QUALIFY ROW_NUMBER() OVER (PARTITION BY a ORDER BY b DESC) = 1` (sem o `a` no `ORDER BY` final) |
| `JOIN LATERAL (SELECT ... WHERE t.x = o.x ORDER BY ... LIMIT 1) l ON TRUE` | CTE com `QUALIFY ROW_NUMBER() OVER (PARTITION BY x ORDER BY ...) = 1` + `LEFT JOIN` |
| `x IS TRUE` / `IS FALSE` | `x = TRUE` / `x = FALSE` (atenção: com `NULL`, `IS FALSE` do PG é falso e `= FALSE` do SF é NULL, com o mesmo efeito dentro de `WHEN`/`WHERE`) |
| `ILIKE` | igual |
| `unaccent(x)` | `TRANSLATE(x, 'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ', 'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC')` |
| `NULLS LAST` | igual |
| `%(nome)s` | igual (connector em `paramstyle=pyformat`) |
| `= ANY(%(lista)s)` | `IN (%(lista)s)` com o parâmetro passado como tupla |

Nomes sem aspas: o Snowflake guarda em MAIÚSCULA e compara case-insensitive, então o texto em minúscula funciona. `database.py` já devolve as chaves em minúscula.

Fluxo por router: portar tudo → `pytest tests/parity -q -k <router>` → corrigir até 100% → commit. Para depurar uma divergência, rode a query dos dois lados com os mesmos parâmetros e compare o `EXCEPT` no Snowflake contra um parquet do PG, ou só as contagens por grupo.

---

### Task 12: Porte `fornecedores.py` (3 endpoints)

**Files:** Modify: `backend/api/fornecedores.py`

- [ ] **Step 1: Exemplo completo — `mapa-por-uf`**

A CTE usa `BTRIM` e o `SELECT` usa `FILTER`. Porte:

```python
    query = Q(
        pg=PG_MAPA_POR_UF,
        sf="""
        WITH compras_classificadas AS (
            SELECT
                COALESCE(NULLIF(TRIM(mun.sigla_uf), ''), 'Nao informado') AS uf,
                CASE
                    WHEN ce.nacional_estrangeiro = 'ESTRANGEIRO' THEN 'ESTRANGEIRO'
                    WHEN ce.possui_socio_pj_exterior = TRUE THEN 'GRUPO_ESTRANGEIRO'
                    WHEN ce.nacional_estrangeiro = 'NACIONAL'
                         AND ce.possui_socio_pj_exterior = FALSE THEN 'NACIONAL'
                    ELSE 'DESCONHECIDO'
                END AS origem,
                c.quantidade_de_itens,
                c.preco_total
            FROM mantenedora_compra_produto c
            JOIN mantenedora m ON m.mantenedora_id = c.mantenedora_id
            LEFT JOIN municipio mun ON mun.codigo_do_municipio = m.municipio_id
            LEFT JOIN fornecedor f ON f.fornecedor_id = c.fornecedor_id
            LEFT JOIN cnpj_enriquecido ce ON ce.cnpj = TRIM(f.cnpj_fornecedor)
            WHERE c.data_de_compra >= %(data_inicio)s
              AND c.data_de_compra < %(data_fim_exclusiva)s
        )
        SELECT
            uf,
            COALESCE(SUM(IFF(origem = 'NACIONAL', quantidade_de_itens, NULL)), 0) AS quantidade_nacional,
            COALESCE(SUM(IFF(origem = 'ESTRANGEIRO', quantidade_de_itens, NULL)), 0) AS quantidade_estrangeiro,
            COALESCE(SUM(IFF(origem = 'GRUPO_ESTRANGEIRO', quantidade_de_itens, NULL)), 0) AS quantidade_grupo_estrangeiro,
            COALESCE(SUM(IFF(origem = 'DESCONHECIDO', quantidade_de_itens, NULL)), 0) AS quantidade_desconhecida,
            COALESCE(SUM(IFF(origem = 'NACIONAL', preco_total, NULL)), 0) AS valor_nacional,
            COALESCE(SUM(IFF(origem = 'ESTRANGEIRO', preco_total, NULL)), 0) AS valor_estrangeiro,
            COALESCE(SUM(IFF(origem = 'GRUPO_ESTRANGEIRO', preco_total, NULL)), 0) AS valor_grupo_estrangeiro,
            COALESCE(SUM(IFF(origem = 'DESCONHECIDO', preco_total, NULL)), 0) AS valor_desconhecido
        FROM compras_classificadas
        GROUP BY uf
        ORDER BY uf
        """,
    )
```

Mova o texto Postgres original para uma constante de módulo `PG_MAPA_POR_UF = """..."""`, sem alterar nada, e passe `query` a `fetch_all` como antes. Faça o mesmo para `ranking` (o fragmento `filtro_uf` vira `_filtro_uf(engine)`, com `TRIM` no Snowflake e `BTRIM` no PG) e para `top-por-uf`.

- [ ] **Step 2: Paridade do router**

Run: `.venv/bin/pytest tests/parity -q -k fornecedores`
Expected: `4 passed`.

- [ ] **Step 3: Commit**

```bash
git add backend/api/fornecedores.py
git commit -m "feat(dashboard): fornecedores em Snowflake (paridade 4/4)"
```

---

### Task 13: Porte `compras.py` (7 endpoints)

**Files:** Modify: `backend/api/compras.py`

- [ ] **Step 1: Portar**

`_montar_filtros` só usa SQL portável (comparações, `IN (SELECT ...)`, `=`), então continua igual e é usado pelos dois engines. Porte cada uma das 7 queries seguindo as regras. `DATE_TRUNC(...)::date` (linhas ~172 e ~194) fica igual. Revise cada `COALESCE(NULLIF(BTRIM(...)))` → `TRIM`.

- [ ] **Step 2: Paridade**

Run: `.venv/bin/pytest tests/parity -q -k compras`
Expected: `8 passed`.

- [ ] **Step 3: Commit**

```bash
git add backend/api/compras.py
git commit -m "feat(dashboard): compras em Snowflake (paridade 8/8)"
```

---

### Task 14: Porte `medicamentos.py` (9 endpoints)

**Files:** Modify: `backend/api/medicamentos.py`

- [ ] **Step 1: `DISTINCT ON` do estoque (`resumo`, `lotes-vencendo`, `estoque-por-uf`)**

A CTE `ultima_posicao`/`estoque_atual` no PG:

```sql
SELECT DISTINCT ON (iep.instituicao_id) iep.* ...
FROM instituicao_estoca_produto iep
INNER JOIN produtos_catmat p ON p.produto_id = iep.produto_id
ORDER BY iep.instituicao_id, iep.data_de_posicao_no_estoque DESC NULLS LAST, iep.instituicao_estoca_produto_id DESC
```

vira no Snowflake:

```sql
SELECT iep.* ...
FROM instituicao_estoca_produto iep
INNER JOIN produtos_catmat p ON p.produto_id = iep.produto_id
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY iep.instituicao_id
    ORDER BY iep.data_de_posicao_no_estoque DESC NULLS LAST, iep.instituicao_estoca_produto_id DESC
) = 1
```

Mantenha a lista de colunas exatamente como no original. Em `lotes-vencendo`, `ea.data_de_validade::date + (%(dias)s * INTERVAL '1 day')` vira `DATEADD(day, %(dias)s, ea.data_de_validade::date)`.

- [ ] **Step 2: Demais queries**

`busca`, `produtos`, `evolucao-preco`, `compras/fornecedores`, `compras/fabricantes` e `compras` (histórico com `LIMIT/OFFSET`, que é igual no Snowflake): aplique as regras.

- [ ] **Step 3: Paridade**

Run: `.venv/bin/pytest tests/parity -q -k medicamentos`
Expected: `9 passed`.

- [ ] **Step 4: Commit**

```bash
git add backend/api/medicamentos.py
git commit -m "feat(dashboard): medicamentos em Snowflake (paridade 9/9)"
```

---

### Task 15: Porte `leitos.py` (9 endpoints) e fechamento da paridade

**Files:** Modify: `backend/api/leitos.py`

- [ ] **Step 1: Inventário do que é específico do PG**

Run: `grep -nE "FILTER \(|BTRIM|DISTINCT ON|LATERAL|INTERVAL|IS (TRUE|FALSE)|::|ANY\(|unaccent|generate_series|to_char" backend/api/leitos.py`
Expected: a lista de pontos a portar (o `JOIN LATERAL` do backend está aqui). `generate_series(a, b, interval '1 month')`, se aparecer, vira `SELECT DATEADD(month, SEQ4(), a) FROM TABLE(GENERATOR(ROWCOUNT => 1000)) QUALIFY ... <= b` ou uma CTE de meses a partir de `DISTINCT DATE_TRUNC('month', competencia)`. Prefira a segunda forma e confirme na paridade. `to_char(d, 'YYYY-MM')` vira `TO_CHAR(d, 'YYYY-MM')`, que é igual.

- [ ] **Step 2: Portar, incluindo os fragmentos de filtro (`modo`, `uf`) com `engine`**

- [ ] **Step 3: Paridade completa**

Run: `.venv/bin/pytest tests/parity -q && cat tests/parity/report.md | tail -1`
Expected: todos os casos passam e o relatório fecha com `**31/31 iguais**` (28 endpoints + 3 casos extras de filtro).

- [ ] **Step 4: Smoke do front contra o Snowflake**

```bash
DB_ENGINE=snowflake .venv/bin/uvicorn backend.main:app --port 8000 &
(cd frontend && npx playwright test)
```

Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/api/leitos.py tests/parity/report.md
git commit -m "feat(dashboard): leitos em Snowflake; paridade completa"
```

---

### Task 16: Deploy no Mod. de Inteligência demo2

**Files:** Create: `deploy/dadosfera_client.py` (cópia), `deploy/deploy_service.py`, `deploy/environment_setup.sh`, `deploy/verify.py`, `deploy/README.md`; `deploy/manifest.json` é gerado

Fonte do padrão: `/Users/allansene/Repos/dadosfera/kine-gest-ddf-oic/apps/oic-visitors/deploy/`.

- [ ] **Step 1: Copiar o cliente**

```bash
cp /Users/allansene/Repos/dadosfera/kine-gest-ddf-oic/apps/oic-visitors/deploy/dadosfera_client.py deploy/
cp /Users/allansene/Repos/dadosfera/kine-gest-ddf-oic/apps/oic-visitors/deploy/deploy_service.py deploy/
```

O `dadosfera_client.py` faz login no Maestro com `DADOSFERADEMO_USER`/`DADOSFERADEMO_PASSWORD`, lidos de `DADOSFERA_ENV_FILE`. Use `DADOSFERA_ENV_FILE=/Users/allansene/Repos/dadosfera/ai-cto-assistants/.env`.

- [ ] **Step 2: `deploy/environment_setup.sh`**

```bash
#!/bin/bash
# Ambiente do data app Dashboard DATASUS (imagem dadosfera/base-kernel-py, Python 3.9). Só pip.
set -e
pip3 install --upgrade pip
pip3 install -r /project-dir/backend/requirements.txt
```

- [ ] **Step 3: Adaptar `deploy/deploy_service.py`**

Mudanças em relação ao original do OIC:

```python
ROOT = Path(__file__).resolve().parents[1]           # Dashboard/
PROJECT = os.getenv("EMBRAPII_PROJECT_NAME", "embrapii-dashboard-datasus")
PROJECT_DESCRIPTION = ("Dashboard Dados em Saúde (projeto EMBRAPII DCC/UFMG): medicamentos, compras, leitos e "
                       "fornecedores do DATASUS. Lê o Snowflake EMBRAPII_DATASUS.")
ENV_NAME = "embrapii-dashboard"
SERVICE = "dataapp"; PORT = 8000; PIPELINE = "embrapii_dataapp"
OUT = ROOT / "frontend" / "dist"
UPLOAD_ROOTS = [ROOT / "backend"]                     # sobe backend/ inteiro (lição Porto)
EXCLUDE = ("__pycache__", "tests", ".pytest_cache", ".ruff_cache")
```

- Lista de upload: todos os arquivos de `backend/` (exceto `EXCLUDE`, `.env` e arquivos que começam com `.`), mais `frontend/dist/**`. Os caminhos no projeto são `backend/...` e `frontend/dist/...`.
- `service_doc`: `"args": f"-c 'umask 002 && cd /project-dir && uvicorn backend.main:app --host 0.0.0.0 --port {PORT}'"` e

```python
"env_variables": {
    "DB_ENGINE": "snowflake",
    "SNOWFLAKE_SECRET_ID": SECRET_ID,
    "SNOWFLAKE_SCHEMA": "EMBRAPII_DATASUS",
    "FRONTEND_DIST": "/project-dir/frontend/dist",
    "APP_BASE_PATH": f"/$BASE_PATH_PREFIX_{PORT}",
    "QUERY_CACHE_TTL_SECONDS": "3600",
},
```

- O build do front roda sem variável de prefixo (`npm run build`), porque o prefixo chega em runtime.
- Remova do original o que é específico do OIC: SDK, WASM, pré-voo do upload grande e `SNAPSHOT_DIR`.
- Mantenha: criação de projeto com `description`, ambiente com poll em `/catch/api-proxy/api/environment-builds/most-recent/<project_uuid>`, pipeline com o serviço, DELETE + create do standalone service e gravação do `manifest.json`.

- [ ] **Step 4: `deploy/verify.py`**

```python
#!/usr/bin/env python3
"""Verifica o data app publicado: health, engine e um GET com dado por router."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dadosfera_client import Dadosfera  # noqa: E402

M = json.loads((Path(__file__).parent / "manifest.json").read_text())
URL = M["dataapp_url"].rstrip("/")
CHECKS = [
    ("/health", lambda j: j.get("status") == "ok"),
    ("/health/database", lambda j: j.get("engine") == "snowflake" and j.get("status") == "ok"),
    ("/api/leitos/opcoes", lambda j: bool(j)),
    ("/api/medicamentos/busca?q=dipirona&limite=5", lambda j: len(j) > 0),
    ("/api/compras/kpis?data_inicio=2024-01-01&data_fim=2024-12-31", lambda j: bool(j)),
    ("/api/fornecedores/mapa-por-uf?data_inicio=2024-01-01&data_fim=2024-12-31", lambda j: len(j) > 0),
]


def main() -> None:
    d = Dadosfera(); d.login()
    ok = True
    for path, check in CHECKS:
        r = d.raw("GET", URL + path, timeout=120)
        good = r.status_code == 200 and check(r.json())
        ok &= good
        print(("OK  " if good else "FAIL"), r.status_code, path)
    r = d.raw("GET", URL + "/", timeout=60)
    good = r.status_code == 200 and "window.__APP_BASE__" in r.text
    ok &= good
    print(("OK  " if good else "FAIL"), r.status_code, "/ (index com prefixo)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Deploy**

```bash
(cd frontend && npm run build)
DADOSFERA_ENV_FILE=/Users/allansene/Repos/dadosfera/ai-cto-assistants/.env .venv/bin/python deploy/deploy_service.py --start
```

Expected: `manifest.json` com `project_uuid`, `dataapp_url` e `standalone_service_uuid`. O build do ambiente leva de 5 a 15 min. Se o pod entrar em CrashLoopBackOff, quase sempre falta arquivo no upload: confira a lista de upload no log.

- [ ] **Step 6: Verificar**

```bash
DADOSFERA_ENV_FILE=/Users/allansene/Repos/dadosfera/ai-cto-assistants/.env .venv/bin/python deploy/verify.py
```

Expected: todas as linhas `OK`. Depois rode o smoke contra a URL publicada, com o cookie de SSO. Se o Playwright cair na tela de login do app.dadosfera.ai, reaproveite o login Playwright do Porto (memória `demo-lakehouse-porto`: login no app.dadosfera.ai, cookies `ddf-auth` servem para o Orchest):

```bash
cd frontend && E2E_BASE_URL="$(python3 -c 'import json;print(json.load(open("../deploy/manifest.json"))["dataapp_url"])')" npx playwright test
```

- [ ] **Step 7: `deploy/README.md` e commit**

O `deploy/README.md` documenta, em até 25 linhas: pré-requisitos (`.env` do ai-cto-assistants, `frontend/dist` buildado), os dois comandos (deploy e verify) e as variáveis de ambiente do serviço.

```bash
git add deploy/
git commit -m "feat(dashboard): deploy no Modulo de Inteligencia demo2"
```

---

### Task 17: Report de revisão de UX (gate)

**Files:** Create: `docs/ux-review/index.html`, `docs/ux-review/shots/*.png`, `docs/ux-review/capture.ts`

- [ ] **Step 1: Prints das 6 páginas, estado padrão e um estado com filtro, em 1440×900**

`docs/ux-review/capture.ts` (roda com `npx tsx`, a partir de `frontend/`, contra o app local em Snowflake):

```ts
import { chromium } from "@playwright/test";

const BASE = process.env.E2E_BASE_URL ?? "http://localhost:8000/";
const PAGES = ["", "medicamentos", "compras", "leitos", "mapa", "fornecedores"];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  for (const p of PAGES) {
    await page.goto(BASE + p);
    await page.waitForLoadState("networkidle");
    await page.screenshot({ path: `../docs/ux-review/shots/${p || "home"}.png`, fullPage: true });
  }
  await browser.close();
})();
```

Run: `cd frontend && npx tsx ../docs/ux-review/capture.ts`
Expected: 6 PNGs em `docs/ux-review/shots/`. Para Medicamentos e Compras, capture também o estado depois de buscar "dipirona": acrescente as interações lendo os seletores das páginas.

- [ ] **Step 2: Escrever o report com a skill `build-report` (HTML Beast)**

Por página: print, problemas encontrados (hierarquia visual, KPIs, filtros, tabelas, estados vazio, erro e carregamento), proposta e esforço (P/M/G). Fecha com uma lista de pendências que exigiriam endpoint novo, que não serão implementadas. Passe o texto pela skill `sem-slop` antes de entregar.

- [ ] **Step 3: Commit e push**

```bash
git add docs/ux-review/
git commit -m "docs(dashboard): report de revisao de UX para aprovacao"
git push -u origin feat/dadosfera-dataapp
```

- [ ] **Step 4: Entregar ao Allan**

Mande o link `file:///Users/allansene/Repos/dadosfera/project-embrapii/Dashboard/docs/ux-review/index.html`, a URL do data app no demo2 e o `tests/parity/report.md`. **Pare aqui.** O Plano B (Beast + UX aprovada + Catálogo + PR) é escrito a partir das decisões dele sobre o report.
