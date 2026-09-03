"""Adapter do XiYanSQL com idioma de prompt delimitado por operação."""

from __future__ import annotations

from contextlib import contextmanager
import os
from typing import Iterator

from interface.backend.adapters.base import AdapterBehavior, BaseGeneratorAdapter
from interface.backend.domain.capabilities import LibraryId


_PROMPT_LANGUAGE_ENV = "XIYAN_PROMPT_LANG"


@contextmanager
def xiyan_prompt_language() -> Iterator[None]:
    existed = _PROMPT_LANGUAGE_ENV in os.environ
    previous = os.environ.get(_PROMPT_LANGUAGE_ENV)
    os.environ[_PROMPT_LANGUAGE_ENV] = "cn"
    try:
        yield
    finally:
        if existed and previous is not None:
            os.environ[_PROMPT_LANGUAGE_ENV] = previous
        else:
            os.environ.pop(_PROMPT_LANGUAGE_ENV, None)


def _load_xiyan_sql(**kwargs):
    from src.xiyansql import XiYanSQL

    return XiYanSQL(**kwargs)


class XiYanSQLAdapter(BaseGeneratorAdapter):
    library = LibraryId.XIYAN_SQL
    behavior = AdapterBehavior(generation_may_execute_sql=False)

    def _adapter_operation_scope(self):
        return xiyan_prompt_language()

    def _constructor_kwargs(self, db_config: dict[str, object]) -> dict[str, object]:
        return {
            "db_config": db_config,
            "model_id": self.configuration.model_id,
            "hf_token": self._hf_token,
            "local_model": True,
            "doc_path": self.resources.doc_path,
            "examples_path": self.resources.examples_path,
        }


DEFAULT_GENERATOR_FACTORY = _load_xiyan_sql
