# M-Schema (vendorizado)

Cópia de [XGenerationLab/M-Schema](https://github.com/XGenerationLab/M-Schema)
(branch `main`), usada para gerar a representação **M-Schema** do esquema do
banco no método XiYanSQL ([src/xiyansql.py](../../xiyansql.py)).

- **Licença:** Apache-2.0 (ver [LICENSE](LICENSE)).
- **Por que vendorizar:** o M-Schema não é publicado no PyPI; o uso é copiar os
  arquivos. Mantemos isso aqui em vez de adicionar dependência git.

## Uso

```python
from src.vendor.m_schema import SchemaEngine
mschema_str = SchemaEngine(engine=sqlalchemy_engine, db_name=db_name).mschema.to_mschema()
```

Suporta SQLite e PostgreSQL (entre outros), cobrindo todos os bancos do projeto.

## Adaptações em relação ao upstream (todas marcadas com `# [VENDOR]`)

1. **`schema_engine.py`** — `from llama_index.core import SQLDatabase` foi
   trocado por `from .sqldatabase import SQLDatabase` (shim local), eliminando a
   dependência `llama-index`. Os imports planos (`from utils import ...`,
   `from m_schema import ...`) viraram relativos.
2. **`schema_engine.py`** — removidos os 5 `print("Debug: ...")` de
   `init_mschema` (poluíam a saída do pipeline).
3. **`m_schema.py`** — import plano `from utils import ...` → relativo.
4. **`sqldatabase.py`** (novo) — shim em SQLAlchemy puro que replica os atributos
   de `llama_index.core.SQLDatabase` usados pelo `SchemaEngine` (`_engine`,
   `_inspector`, `_usable_tables`, `metadata_obj`).
5. **`__init__.py`** (novo) — expõe `SchemaEngine` e `MSchema`.

Arquivos do upstream não usados (`example.py`, `aan_1.sqlite`, `pyproject.toml`,
`uv.lock`, `.python-version`) não foram trazidos. `requirements.txt` foi mantido
apenas como referência (as únicas dependências reais do código vendorizado são
`sqlalchemy`, já presente no projeto).

## Como atualizar

Rebaixar os `.py` do repositório upstream e reaplicar as adaptações 1–3 acima
(o shim e os `__init__` são locais e não vêm do upstream).
