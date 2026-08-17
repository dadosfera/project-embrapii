"""Fakes puros compartilhados pelos testes dos adapters."""

from __future__ import annotations

import os
from pathlib import Path

from interface.backend.domain.capabilities import ConfigurationSelection


GENERAL_MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
XIYAN_MODEL_ID = "XGenerationLab/XiYanSQL-QwenCoder-3B-2504"


def configuration(
    library: str = "raw_model",
    context: str = "default",
    model_id: str = GENERAL_MODEL_ID,
    database: str = "sih_database",
) -> ConfigurationSelection:
    return ConfigurationSelection(
        database=database,
        library=library,
        model_id=model_id,
        context=context,
    )


def create_context_files(root: Path, database: str = "sih_database") -> None:
    create_project_root(root)
    directory = root / "datasets" / database
    directory.mkdir(parents=True, exist_ok=True)
    if database == "sih_database":
        documentation = directory / "sih_documentation_resumida.md"
        examples = directory / "exemplos.json"
    else:
        documentation = directory / "datasus_documentation_resumida.md"
        examples = directory / "consultas_exemplo_reduzido.json"
    documentation.write_text("documentação sintética", encoding="utf-8")
    examples.write_text("[]", encoding="utf-8")


class FakeGenerator:
    def __init__(
        self,
        *,
        output: object = "synthetic-output",
        generation_error: Exception | None = None,
    ) -> None:
        self.output = output
        self.generation_error = generation_error
        self.questions: list[str] = []
        self.prompt_languages: list[str | None] = []
        self.generation_directories: list[Path] = []

    def generate_query(self, question: str) -> object:
        self.questions.append(question)
        self.prompt_languages.append(os.environ.get("XIYAN_PROMPT_LANG"))
        self.generation_directories.append(Path.cwd())
        if self.generation_error is not None:
            raise self.generation_error
        return self.output


class RecordingFactory:
    def __init__(
        self,
        *,
        output: object = "synthetic-output",
        constructor_error: Exception | None = None,
        generation_error: Exception | None = None,
        events: list[str] | None = None,
    ) -> None:
        self.output = output
        self.constructor_error = constructor_error
        self.generation_error = generation_error
        self.events = events
        self.calls: list[dict[str, object]] = []
        self.prompt_languages: list[str | None] = []
        self.constructor_directories: list[Path] = []
        self.generator: FakeGenerator | None = None

    def __call__(self, **kwargs) -> FakeGenerator:
        if self.events is not None:
            self.events.append("construct")
        self.calls.append(kwargs)
        self.prompt_languages.append(os.environ.get("XIYAN_PROMPT_LANG"))
        self.constructor_directories.append(Path.cwd())
        if self.constructor_error is not None:
            raise self.constructor_error
        self.generator = FakeGenerator(
            output=self.output,
            generation_error=self.generation_error,
        )
        return self.generator


class DependencyRecorder:
    def __init__(self, events: list[str] | None = None) -> None:
        self.events = events
        self.seed_calls: list[int] = []
        self.database_calls: list[str] = []
        self.db_config = {"SGBD": "synthetic", "database_marker": object()}

    def set_seed(self, value: int) -> None:
        if self.events is not None:
            self.events.append("seed")
        self.seed_calls.append(value)

    def resolve_database(self, database: str) -> dict[str, object]:
        if self.events is not None:
            self.events.append("database")
        self.database_calls.append(database)
        return self.db_config


def create_project_root(root: Path) -> Path:
    """Cria somente o cache sintético mínimo exigido pelo workspace."""

    (root / "local_models").mkdir(parents=True, exist_ok=True)
    return root
