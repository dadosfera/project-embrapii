"""Adapter da VannaAI legada."""

from __future__ import annotations

from interface.backend.adapters.base import AdapterBehavior, BaseGeneratorAdapter
from interface.backend.adapters.release import release_vanna_generator
from interface.backend.domain.capabilities import LibraryId
from interface.backend.diagnostics import log_runtime_event


def _load_vanna_ai(**kwargs):
    from src.vannaai import VannaAi

    return VannaAi(**kwargs)


class VannaAIAdapter(BaseGeneratorAdapter):
    library = LibraryId.VANNA_AI
    behavior = AdapterBehavior(generation_may_execute_sql=False)

    def _constructor_kwargs(self, db_config: dict[str, object]) -> dict[str, object]:
        return {
            "db_config": db_config,
            "model_id": self.configuration.model_id,
            "hf_token": self._hf_token,
            "local_model": True,
            "doc_path": self.resources.doc_path,
            "examples_path": self.resources.examples_path,
            "runtime_diagnostics": self._runtime_diagnostic,
        }

    def _runtime_diagnostic(self, event: str, **fields: object) -> None:
        exception = fields.pop("exception", None)
        log_runtime_event(
            event,
            stage=fields.pop("stage", event),
            exception=exception if isinstance(exception, BaseException) else None,
            **fields,
        )

    def _release_generator(self, generator) -> None:
        release_vanna_generator(generator)


DEFAULT_GENERATOR_FACTORY = _load_vanna_ai
