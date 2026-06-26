"""
[VENDOR] Substituição mínima de `llama_index.core.SQLDatabase`.

O `SchemaEngine` do M-Schema (upstream) herda de `llama_index.core.SQLDatabase`
apenas para obter quatro coisas via SQLAlchemy: o `engine`, o `inspector`, a
lista de tabelas utilizáveis (`_usable_tables`) e um objeto `MetaData`
(`metadata_obj`). Para evitar trazer a dependência pesada `llama-index` (e
possíveis conflitos com os pins de `transformers`/`huggingface-hub` do projeto),
replicamos aqui exatamente esse comportamento com SQLAlchemy puro.

Mantém a mesma assinatura de `__init__` usada pelo `SchemaEngine`.
Ver `VENDOR.md` para o registro completo das adaptações.
"""
from typing import List, Optional

from sqlalchemy import MetaData
from sqlalchemy import inspect as sqla_inspect
from sqlalchemy.engine import Engine


class SQLDatabase:
    def __init__(
        self,
        engine: Engine,
        schema: Optional[str] = None,
        metadata: Optional[MetaData] = None,
        ignore_tables: Optional[List[str]] = None,
        include_tables: Optional[List[str]] = None,
        sample_rows_in_table_info: int = 3,
        indexes_in_table_info: bool = False,
        custom_table_info: Optional[dict] = None,
        view_support: bool = False,
        max_string_length: int = 300,
    ):
        self._engine = engine
        self._schema = schema
        self._inspector = sqla_inspect(engine)
        self._metadata = metadata or MetaData()
        self.metadata_obj = self._metadata
        self._sample_rows_in_table_info = sample_rows_in_table_info
        self._indexes_in_table_info = indexes_in_table_info
        self._custom_table_info = custom_table_info
        self._view_support = view_support
        self._max_string_length = max_string_length

        if include_tables and ignore_tables:
            raise ValueError("Use 'include_tables' ou 'ignore_tables', não ambos.")

        tables = list(self._inspector.get_table_names(schema=schema))
        if view_support:
            tables += list(self._inspector.get_view_names(schema=schema))

        if include_tables:
            include = set(include_tables)
            tables = [t for t in tables if t in include]
        if ignore_tables:
            ignore = set(ignore_tables)
            tables = [t for t in tables if t not in ignore]

        # O SchemaEngine recalcula esta lista após o super().__init__()
        # conforme o schema resolvido (ex.: 'public' no PostgreSQL).
        self._usable_tables = tables

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def inspector(self):
        return self._inspector
