"""Adapter do PremSQLAgent legado, restrito ao Benchmark."""

from __future__ import annotations

from interface.backend.adapters.base import AdapterBehavior, BaseGeneratorAdapter
from interface.backend.domain.capabilities import LibraryId


def _load_premsql_agent(**kwargs):
    from src.premsqlAgente import PremSQLAgent

    return PremSQLAgent(**kwargs)


class PremSQLAdapter(BaseGeneratorAdapter):
    library = LibraryId.PREMSQL_AGENT
    behavior = AdapterBehavior(generation_may_execute_sql=True)

    def _constructor_kwargs(self, db_config: dict[str, object]) -> dict[str, object]:
        return {
            "db_config": db_config,
            "model_id": self.configuration.model_id,
            "hf_token": self._hf_token,
            "local_model": True,
        }


DEFAULT_GENERATOR_FACTORY = _load_premsql_agent
