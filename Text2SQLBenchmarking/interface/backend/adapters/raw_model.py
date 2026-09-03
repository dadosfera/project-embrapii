"""Adapter do RawModel legado."""

from __future__ import annotations

from interface.backend.adapters.base import AdapterBehavior, BaseGeneratorAdapter
from interface.backend.adapters.release import release_raw_model_generator
from interface.backend.domain.capabilities import LibraryId


def _load_raw_model(**kwargs):
    from src.rawmodel import RawModel

    return RawModel(**kwargs)


class RawModelAdapter(BaseGeneratorAdapter):
    library = LibraryId.RAW_MODEL
    behavior = AdapterBehavior(generation_may_execute_sql=False)

    def _constructor_kwargs(self, db_config: dict[str, object]) -> dict[str, object]:
        return {
            "db_config": db_config,
            "model_id": self.configuration.model_id,
            "hf_token": self._hf_token,
            "local_model": True,
            "examples_path": self.resources.examples_path,
            "examples_seed": self.random_seed,
        }

    def _release_generator(self, generator) -> None:
        release_raw_model_generator(generator)


DEFAULT_GENERATOR_FACTORY = _load_raw_model
