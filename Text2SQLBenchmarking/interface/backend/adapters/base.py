"""Contrato uniforme dos adapters sem importar a infraestrutura científica."""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager, contextmanager, nullcontext
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol

from interface.backend.adapters.paths import ContextResources
from interface.backend.adapters.workspace import RuntimeWorkspace
from interface.backend.adapters.release import cleanup_compute_memory, release_legacy_references
from interface.backend.domain.capabilities import (
    ApplicationMode,
    ConfigurationSelection,
    LibraryId,
)


class AdapterErrorCode(str, Enum):
    ADAPTER_NOT_LOADED = "ADAPTER_NOT_LOADED"
    ADAPTER_ALREADY_LOADED = "ADAPTER_ALREADY_LOADED"
    ADAPTER_LOAD_ERROR = "ADAPTER_LOAD_ERROR"
    ADAPTER_GENERATION_ERROR = "ADAPTER_GENERATION_ERROR"
    ADAPTER_INVALID_OUTPUT = "ADAPTER_INVALID_OUTPUT"
    ADAPTER_RELEASE_ERROR = "ADAPTER_RELEASE_ERROR"
    CONTEXT_RESOURCE_NOT_FOUND = "CONTEXT_RESOURCE_NOT_FOUND"
    RUNTIME_WORKSPACE_ERROR = "RUNTIME_WORKSPACE_ERROR"
    UNSUPPORTED_COMBINATION = "UNSUPPORTED_COMBINATION"


class AdapterError(Exception):
    """Erro estruturado com mensagem pública separada do diagnóstico interno."""

    def __init__(
        self,
        code: AdapterErrorCode,
        public_message: str,
        internal_detail: str,
    ) -> None:
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message
        self.internal_detail = internal_detail


@dataclass(frozen=True)
class AdapterBehavior:
    generation_may_execute_sql: bool


@dataclass(frozen=True)
class GenerationResult:
    sql: str
    library: LibraryId
    configuration: ConfigurationSelection
    mode: ApplicationMode
    random_seed: int
    behavior: AdapterBehavior


class LegacyGenerator(Protocol):
    def generate_query(self, question: str) -> object: ...


GeneratorFactory = Callable[..., LegacyGenerator]
DatabaseConfigResolver = Callable[[str], dict[str, object]]
SeedSetter = Callable[[int], None]


def resolve_database_config_from_pipeline(database: str) -> dict[str, object]:
    """Importa o registry somente quando ``load()`` for realmente executado."""

    from src.utilitis import get_db_config

    db_config, _ = get_db_config(database)
    if not isinstance(db_config, dict):
        raise ValueError("database sem configuração no pipeline")
    return db_config


def set_pipeline_seed(random_seed: int) -> None:
    """Reutiliza a mesma função de seed do pipeline por importação tardia."""

    from src.utilitis import set_seed

    set_seed(random_seed)


class BaseGeneratorAdapter(ABC):
    """Ciclo uniforme que preserva a chamada específica de cada gerador."""

    library: LibraryId
    behavior: AdapterBehavior

    def __init__(
        self,
        *,
        configuration: ConfigurationSelection,
        mode: ApplicationMode,
        registry_name: str,
        random_seed: int,
        hf_token: str | None,
        resources: ContextResources,
        workspace: RuntimeWorkspace,
        generator_factory: GeneratorFactory,
        database_config_resolver: DatabaseConfigResolver = resolve_database_config_from_pipeline,
        seed_setter: SeedSetter = set_pipeline_seed,
    ) -> None:
        self.configuration = configuration
        self.mode = mode
        self.registry_name = registry_name
        self.random_seed = random_seed
        self.resources = resources
        self.workspace = workspace
        self._hf_token = hf_token
        self._generator_factory = generator_factory
        self._database_config_resolver = database_config_resolver
        self._seed_setter = seed_setter
        self._generator: LegacyGenerator | None = None

    @property
    def is_loaded(self) -> bool:
        return self._generator is not None

    def _adapter_operation_scope(self) -> AbstractContextManager[None]:
        return nullcontext()

    @contextmanager
    def _operation_scope(self):
        """Combina o cwd isolado com escopos específicos da biblioteca."""

        with self.workspace.activate():
            with self._adapter_operation_scope():
                yield

    @abstractmethod
    def _constructor_kwargs(
        self,
        db_config: dict[str, object],
    ) -> dict[str, object]:
        """Argumentos exatos aceitos pela classe legada."""

    def load(self) -> None:
        if self.is_loaded:
            raise AdapterError(
                AdapterErrorCode.ADAPTER_ALREADY_LOADED,
                "O gerador já está carregado.",
                "load chamado com referência de gerador existente",
            )

        try:
            self._seed_setter(self.random_seed)
            db_config = self._database_config_resolver(self.configuration.database)
            if not isinstance(db_config, dict):
                raise TypeError("resolver de banco não retornou dict")
            with self._operation_scope():
                generator = self._generator_factory(
                    **self._constructor_kwargs(db_config)
                )
            if generator is None:
                raise TypeError("factory retornou None")
        except AdapterError:
            raise
        except Exception as exc:
            self._generator = None
            raise AdapterError(
                AdapterErrorCode.ADAPTER_LOAD_ERROR,
                "Não foi possível carregar o gerador selecionado.",
                f"falha no load: {type(exc).__name__}",
            ) from exc

        self._generator = generator

    def generate(self, question: str) -> GenerationResult:
        if self._generator is None:
            raise AdapterError(
                AdapterErrorCode.ADAPTER_NOT_LOADED,
                "O gerador ainda não foi carregado.",
                "generate chamado sem referência de gerador",
            )

        try:
            with self._operation_scope():
                output = self._generator.generate_query(question)
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(
                AdapterErrorCode.ADAPTER_GENERATION_ERROR,
                "Não foi possível gerar a consulta.",
                f"falha em generate_query: {type(exc).__name__}",
            ) from exc

        if not isinstance(output, str) or not output.strip():
            raise AdapterError(
                AdapterErrorCode.ADAPTER_INVALID_OUTPUT,
                "O gerador retornou uma consulta vazia ou inválida.",
                f"tipo de saída incompatível: {type(output).__name__}",
            )

        return GenerationResult(
            sql=output,
            library=self.library,
            configuration=self.configuration,
            mode=self.mode,
            random_seed=self.random_seed,
            behavior=self.behavior,
        )

    def _release_generator(self, generator: LegacyGenerator) -> None:
        """Libera objetos legados que retêm pesos, tokenizer, pipeline ou agent."""
        release_legacy_references(generator)

    def release(self) -> None:
        generator = self._generator
        if generator is None:
            cleanup_compute_memory()
            return
        try:
            with self._operation_scope():
                self._release_generator(generator)
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(
                AdapterErrorCode.ADAPTER_RELEASE_ERROR,
                "Não foi possível liberar o gerador corretamente.",
                f"falha no release: {type(exc).__name__}",
            ) from exc
        finally:
            self._generator = None
            cleanup_compute_memory()

    def unload(self) -> None:
        """Alias explícito para o ciclo de vida de runtimes pesados."""
        self.release()
