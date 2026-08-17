"""Catálogo tipado de capacidades expostas pela interface v1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generic, TypeVar


class DatabaseId(str, Enum):
    SIH_DATABASE = "sih_database"
    DATASUS = "datasus"


class DatabaseEngine(str, Enum):
    POSTGRESQL = "postgresql"


class LibraryId(str, Enum):
    RAW_MODEL = "raw_model"
    VANNA_AI = "vanna_ai"
    PREMSQL_AGENT = "premsql_agent"
    XIYAN_SQL = "xiyan_sql"


class ContextId(str, Enum):
    DEFAULT = "default"
    NONE = "none"
    DOCUMENTATION = "documentation"
    EXAMPLES = "examples"
    DOCUMENTATION_AND_EXAMPLES = "documentation_and_examples"


class ModelFamily(str, Enum):
    GENERAL = "general"
    XIYAN = "xiyan"


class ApplicationMode(str, Enum):
    CHAT = "chat"
    BENCHMARK = "benchmark"


class CapabilityErrorCode(str, Enum):
    UNKNOWN_DATABASE = "UNKNOWN_DATABASE"
    UNKNOWN_LIBRARY = "UNKNOWN_LIBRARY"
    UNKNOWN_MODEL = "UNKNOWN_MODEL"
    UNKNOWN_CONTEXT = "UNKNOWN_CONTEXT"
    UNSUPPORTED_COMBINATION = "UNSUPPORTED_COMBINATION"


@dataclass(frozen=True)
class CapabilityError:
    code: CapabilityErrorCode
    message: str


T = TypeVar("T")


@dataclass(frozen=True)
class CatalogResult(Generic[T]):
    """Resultado de domínio sem dependência de HTTP ou exceção genérica."""

    value: T | None = None
    error: CapabilityError | None = None

    @property
    def is_valid(self) -> bool:
        return self.error is None


@dataclass(frozen=True)
class DatabaseCapability:
    id: DatabaseId
    label: str
    engine: DatabaseEngine
    order: int


@dataclass(frozen=True)
class ModelCapability:
    id: str
    label: str
    registry_name: str
    family: ModelFamily
    order: int


@dataclass(frozen=True)
class ContextCapability:
    id: ContextId
    label: str
    order: int


@dataclass(frozen=True)
class UnavailabilityReason:
    code: str
    message: str


@dataclass(frozen=True)
class ModeAvailability:
    available: bool
    reason: UnavailabilityReason | None = None


@dataclass(frozen=True)
class LegacyToken:
    context: ContextId
    token: str


@dataclass(frozen=True)
class LibraryCapability:
    id: LibraryId
    label: str
    model_family: ModelFamily
    contexts: tuple[ContextId, ...]
    legacy_tokens: tuple[LegacyToken, ...]
    chat: ModeAvailability
    benchmark: ModeAvailability
    order: int
    prompt_language: str | None = None


@dataclass(frozen=True)
class ConfigurationSelection:
    database: str
    library: str
    model_id: str
    context: str


@dataclass(frozen=True)
class RegistryValidationIssue:
    registry_name: str
    expected_id: str
    actual_id: str | None
    reason: str


@dataclass(frozen=True)
class RegistryValidationResult:
    valid: bool
    issues: tuple[RegistryValidationIssue, ...]


_AVAILABLE = ModeAvailability(available=True)
_PREMSQL_CHAT_REASON = UnavailabilityReason(
    code="PREMSQL_CHAT_UNAVAILABLE",
    message=(
        "PremSQLAgent não está disponível no Chat nesta versão. "
        "Use-o no modo Benchmark."
    ),
)


_DATABASES = (
    DatabaseCapability(
        id=DatabaseId.SIH_DATABASE,
        label="SIH/DataSUS",
        engine=DatabaseEngine.POSTGRESQL,
        order=1,
    ),
    DatabaseCapability(
        id=DatabaseId.DATASUS,
        label="JABUTI-SQL",
        engine=DatabaseEngine.POSTGRESQL,
        order=2,
    ),
)


_MODELS = (
    ModelCapability(
        id="Qwen/Qwen3-32B",
        label="Qwen 3 32B",
        registry_name="Qwen3-32B",
        family=ModelFamily.GENERAL,
        order=1,
    ),
    ModelCapability(
        id="Qwen/Qwen2.5-Coder-32B-Instruct",
        label="Qwen 2.5 Coder 32B Instruct",
        registry_name="Qwen2.5-Coder-32B-Instruct",
        family=ModelFamily.GENERAL,
        order=2,
    ),
    ModelCapability(
        id="Qwen/Qwen2.5-Coder-14B-Instruct",
        label="Qwen 2.5 Coder 14B Instruct",
        registry_name="Qwen2.5-Coder-14B-Instruct",
        family=ModelFamily.GENERAL,
        order=3,
    ),
    ModelCapability(
        id="Qwen/Qwen2.5-Coder-7B-Instruct",
        label="Qwen 2.5 Coder 7B Instruct",
        registry_name="Qwen2.5-Coder-7B-Instruct",
        family=ModelFamily.GENERAL,
        order=4,
    ),
    ModelCapability(
        id="meta-llama/Llama-3.1-8B-Instruct",
        label="Llama 3.1 8B Instruct",
        registry_name="Llama-3.1-8B-Instruct",
        family=ModelFamily.GENERAL,
        order=5,
    ),
    ModelCapability(
        id="defog/llama-3-sqlcoder-8b",
        label="Llama 3 SQLCoder 8B",
        registry_name="llama-3-sqlcoder-8b",
        family=ModelFamily.GENERAL,
        order=6,
    ),
    ModelCapability(
        id="XGenerationLab/XiYanSQL-QwenCoder-3B-2504",
        label="XiYanSQL QwenCoder 3B (2504)",
        registry_name="XiYanSQL-QwenCoder-3B-2504",
        family=ModelFamily.XIYAN,
        order=7,
    ),
    ModelCapability(
        id="XGenerationLab/XiYanSQL-QwenCoder-7B-2504",
        label="XiYanSQL QwenCoder 7B (2504)",
        registry_name="XiYanSQL-QwenCoder-7B-2504",
        family=ModelFamily.XIYAN,
        order=8,
    ),
    ModelCapability(
        id="XGenerationLab/XiYanSQL-QwenCoder-14B-2504",
        label="XiYanSQL QwenCoder 14B (2504)",
        registry_name="XiYanSQL-QwenCoder-14B-2504",
        family=ModelFamily.XIYAN,
        order=9,
    ),
    ModelCapability(
        id="XGenerationLab/XiYanSQL-QwenCoder-32B-2504",
        label="XiYanSQL QwenCoder 32B (2504)",
        registry_name="XiYanSQL-QwenCoder-32B-2504",
        family=ModelFamily.XIYAN,
        order=10,
    ),
)


_CONTEXTS = (
    ContextCapability(ContextId.DEFAULT, "Configuração padrão", 1),
    ContextCapability(ContextId.NONE, "Sem contexto", 2),
    ContextCapability(ContextId.DOCUMENTATION, "Somente documentação", 3),
    ContextCapability(ContextId.EXAMPLES, "Somente exemplos", 4),
    ContextCapability(
        ContextId.DOCUMENTATION_AND_EXAMPLES,
        "Documentação e exemplos",
        5,
    ),
)


_CONTEXTUAL_CONTEXTS = (
    ContextId.NONE,
    ContextId.DOCUMENTATION,
    ContextId.EXAMPLES,
    ContextId.DOCUMENTATION_AND_EXAMPLES,
)


_LIBRARIES = (
    LibraryCapability(
        id=LibraryId.RAW_MODEL,
        label="RawModel",
        model_family=ModelFamily.GENERAL,
        contexts=(ContextId.DEFAULT, ContextId.EXAMPLES),
        legacy_tokens=(
            LegacyToken(ContextId.DEFAULT, "rawModel"),
            LegacyToken(ContextId.EXAMPLES, "rawModel_exemplos"),
        ),
        chat=_AVAILABLE,
        benchmark=_AVAILABLE,
        order=1,
    ),
    LibraryCapability(
        id=LibraryId.VANNA_AI,
        label="VannaAI",
        model_family=ModelFamily.GENERAL,
        contexts=_CONTEXTUAL_CONTEXTS,
        legacy_tokens=(
            LegacyToken(ContextId.NONE, "vannaAi"),
            LegacyToken(ContextId.DOCUMENTATION, "vannaAi_contexto"),
            LegacyToken(ContextId.EXAMPLES, "vannaAi_exemplos"),
            LegacyToken(
                ContextId.DOCUMENTATION_AND_EXAMPLES,
                "vannaAi_contexto_exemplos",
            ),
        ),
        chat=_AVAILABLE,
        benchmark=_AVAILABLE,
        order=2,
    ),
    LibraryCapability(
        id=LibraryId.PREMSQL_AGENT,
        label="PremSQLAgent",
        model_family=ModelFamily.GENERAL,
        contexts=(ContextId.DEFAULT,),
        legacy_tokens=(LegacyToken(ContextId.DEFAULT, "PremSQLAgente"),),
        chat=ModeAvailability(available=False, reason=_PREMSQL_CHAT_REASON),
        benchmark=_AVAILABLE,
        order=3,
    ),
    LibraryCapability(
        id=LibraryId.XIYAN_SQL,
        label="XiYanSQL",
        model_family=ModelFamily.XIYAN,
        contexts=_CONTEXTUAL_CONTEXTS,
        legacy_tokens=(
            LegacyToken(ContextId.NONE, "XiYanSQL"),
            LegacyToken(ContextId.DOCUMENTATION, "XiYanSQL_contexto"),
            LegacyToken(ContextId.EXAMPLES, "XiYanSQL_exemplos"),
            LegacyToken(
                ContextId.DOCUMENTATION_AND_EXAMPLES,
                "XiYanSQL_contexto_exemplos",
            ),
        ),
        chat=_AVAILABLE,
        benchmark=_AVAILABLE,
        order=4,
        prompt_language="cn",
    ),
)


_DATABASE_BY_ID = {item.id.value: item for item in _DATABASES}
_LIBRARY_BY_ID = {item.id.value: item for item in _LIBRARIES}
_MODEL_BY_ID = {item.id: item for item in _MODELS}
_MODEL_BY_REGISTRY_NAME = {item.registry_name: item for item in _MODELS}
_CONTEXT_BY_ID = {item.id.value: item for item in _CONTEXTS}


_DEFAULT_CONFIGURATION = ConfigurationSelection(
    database=DatabaseId.SIH_DATABASE.value,
    library=LibraryId.RAW_MODEL.value,
    model_id="Qwen/Qwen2.5-Coder-7B-Instruct",
    context=ContextId.DEFAULT.value,
)


def list_databases() -> tuple[DatabaseCapability, ...]:
    return _DATABASES


def list_libraries() -> tuple[LibraryCapability, ...]:
    return _LIBRARIES


def list_models() -> tuple[ModelCapability, ...]:
    return _MODELS


def list_contexts() -> tuple[ContextCapability, ...]:
    return _CONTEXTS


def _error(code: CapabilityErrorCode, message: str) -> CatalogResult[object]:
    return CatalogResult(error=CapabilityError(code=code, message=message))


def list_models_for_library(
    library_id: str,
) -> CatalogResult[tuple[ModelCapability, ...]]:
    library = _LIBRARY_BY_ID.get(library_id)
    if library is None:
        return _error(
            CapabilityErrorCode.UNKNOWN_LIBRARY,
            "A biblioteca informada não existe no catálogo.",
        )
    models = tuple(model for model in _MODELS if model.family is library.model_family)
    return CatalogResult(value=models)


def list_contexts_for_library(
    library_id: str,
) -> CatalogResult[tuple[ContextCapability, ...]]:
    library = _LIBRARY_BY_ID.get(library_id)
    if library is None:
        return _error(
            CapabilityErrorCode.UNKNOWN_LIBRARY,
            "A biblioteca informada não existe no catálogo.",
        )
    contexts = tuple(_CONTEXT_BY_ID[item.value] for item in library.contexts)
    return CatalogResult(value=contexts)


def get_library_availability(
    library_id: str,
    mode: ApplicationMode | str,
) -> CatalogResult[ModeAvailability]:
    library = _LIBRARY_BY_ID.get(library_id)
    if library is None:
        return _error(
            CapabilityErrorCode.UNKNOWN_LIBRARY,
            "A biblioteca informada não existe no catálogo.",
        )
    try:
        selected_mode = ApplicationMode(mode)
    except ValueError:
        return _error(
            CapabilityErrorCode.UNSUPPORTED_COMBINATION,
            "O modo informado não é suportado.",
        )
    availability = library.chat if selected_mode is ApplicationMode.CHAT else library.benchmark
    return CatalogResult(value=availability)


def resolve_model_id(registry_name: str) -> CatalogResult[str]:
    model = _MODEL_BY_REGISTRY_NAME.get(registry_name)
    if model is None:
        return _error(
            CapabilityErrorCode.UNKNOWN_MODEL,
            "O modelo informado não existe no catálogo.",
        )
    return CatalogResult(value=model.id)


def resolve_registry_name(model_id: str) -> CatalogResult[str]:
    model = _MODEL_BY_ID.get(model_id)
    if model is None:
        return _error(
            CapabilityErrorCode.UNKNOWN_MODEL,
            "O modelo informado não existe no catálogo.",
        )
    return CatalogResult(value=model.registry_name)


def resolve_legacy_token(library_id: str, context_id: str) -> CatalogResult[str]:
    library = _LIBRARY_BY_ID.get(library_id)
    if library is None:
        return _error(
            CapabilityErrorCode.UNKNOWN_LIBRARY,
            "A biblioteca informada não existe no catálogo.",
        )
    if context_id not in _CONTEXT_BY_ID:
        return _error(
            CapabilityErrorCode.UNKNOWN_CONTEXT,
            "O contexto informado não existe no catálogo.",
        )
    token = next(
        (item.token for item in library.legacy_tokens if item.context.value == context_id),
        None,
    )
    if token is None:
        return _error(
            CapabilityErrorCode.UNSUPPORTED_COMBINATION,
            "A biblioteca e o contexto informados não são compatíveis.",
        )
    return CatalogResult(value=token)


def validate_configuration(
    configuration: ConfigurationSelection,
    mode: ApplicationMode | str | None = None,
) -> CatalogResult[ConfigurationSelection]:
    if configuration.database not in _DATABASE_BY_ID:
        return _error(
            CapabilityErrorCode.UNKNOWN_DATABASE,
            "A base de dados informada não existe no catálogo.",
        )
    library = _LIBRARY_BY_ID.get(configuration.library)
    if library is None:
        return _error(
            CapabilityErrorCode.UNKNOWN_LIBRARY,
            "A biblioteca informada não existe no catálogo.",
        )
    model = _MODEL_BY_ID.get(configuration.model_id)
    if model is None:
        return _error(
            CapabilityErrorCode.UNKNOWN_MODEL,
            "O modelo informado não existe no catálogo.",
        )
    if configuration.context not in _CONTEXT_BY_ID:
        return _error(
            CapabilityErrorCode.UNKNOWN_CONTEXT,
            "O contexto informado não existe no catálogo.",
        )
    if model.family is not library.model_family:
        return _error(
            CapabilityErrorCode.UNSUPPORTED_COMBINATION,
            "A biblioteca e o modelo informados não são compatíveis.",
        )
    if configuration.context not in {item.value for item in library.contexts}:
        return _error(
            CapabilityErrorCode.UNSUPPORTED_COMBINATION,
            "A biblioteca e o contexto informados não são compatíveis.",
        )
    if mode is not None:
        availability = get_library_availability(configuration.library, mode)
        if not availability.is_valid:
            return CatalogResult(error=availability.error)
        if availability.value is not None and not availability.value.available:
            reason = availability.value.reason
            return _error(
                CapabilityErrorCode.UNSUPPORTED_COMBINATION,
                reason.message if reason else "A combinação informada não está disponível.",
            )
    return CatalogResult(value=configuration)


def get_initial_configuration() -> ConfigurationSelection:
    return _DEFAULT_CONFIGURATION


def validate_against_registry(
    resolver: Callable[[str], str],
) -> RegistryValidationResult:
    """Compara o catálogo ao registry por um resolver puro injetado."""

    issues: list[RegistryValidationIssue] = []
    for model in _MODELS:
        try:
            actual_id = resolver(model.registry_name)
        except Exception as exc:
            issues.append(
                RegistryValidationIssue(
                    registry_name=model.registry_name,
                    expected_id=model.id,
                    actual_id=None,
                    reason=f"resolver levantou {type(exc).__name__}",
                )
            )
            continue
        if actual_id != model.id:
            issues.append(
                RegistryValidationIssue(
                    registry_name=model.registry_name,
                    expected_id=model.id,
                    actual_id=actual_id,
                    reason="model_id divergente",
                )
            )
    return RegistryValidationResult(valid=not issues, issues=tuple(issues))


def serialize_catalog() -> dict[str, object]:
    """Produz dados primitivos para tradução futura pela camada de API."""

    def availability_data(item: ModeAvailability) -> dict[str, object]:
        return {
            "available": item.available,
            "reason": (
                {"code": item.reason.code, "message": item.reason.message}
                if item.reason
                else None
            ),
        }

    return {
        "databases": [
            {
                "id": item.id.value,
                "label": item.label,
                "engine": item.engine.value,
                "order": item.order,
            }
            for item in _DATABASES
        ],
        "libraries": [
            {
                "id": item.id.value,
                "label": item.label,
                "model_family": item.model_family.value,
                "contexts": [context.value for context in item.contexts],
                "legacy_tokens": [
                    {"context": token.context.value, "token": token.token}
                    for token in item.legacy_tokens
                ],
                "availability": {
                    "chat": availability_data(item.chat),
                    "benchmark": availability_data(item.benchmark),
                },
                "prompt_language": item.prompt_language,
                "order": item.order,
            }
            for item in _LIBRARIES
        ],
        "models": [
            {
                "id": item.id,
                "label": item.label,
                "registry_name": item.registry_name,
                "family": item.family.value,
                "order": item.order,
            }
            for item in _MODELS
        ],
        "contexts": [
            {"id": item.id.value, "label": item.label, "order": item.order}
            for item in _CONTEXTS
        ],
        "initial_configuration": {
            "database": _DEFAULT_CONFIGURATION.database,
            "library": _DEFAULT_CONFIGURATION.library,
            "model_id": _DEFAULT_CONFIGURATION.model_id,
            "context": _DEFAULT_CONFIGURATION.context,
        },
    }


def _ensure_unique(values: tuple[str, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise RuntimeError(f"catálogo inválido: {field_name} duplicado")


def _validate_catalog_definition() -> None:
    _ensure_unique(tuple(item.id.value for item in _DATABASES), "database.id")
    _ensure_unique(tuple(item.id.value for item in _LIBRARIES), "library.id")
    _ensure_unique(tuple(item.id for item in _MODELS), "model.id")
    _ensure_unique(tuple(item.label for item in _MODELS), "model.label")
    _ensure_unique(
        tuple(item.registry_name for item in _MODELS),
        "model.registry_name",
    )
    _ensure_unique(tuple(item.id.value for item in _CONTEXTS), "context.id")
    for library in _LIBRARIES:
        token_contexts = tuple(item.context for item in library.legacy_tokens)
        if token_contexts != library.contexts:
            raise RuntimeError(
                f"catálogo inválido: tokens incompletos para {library.id.value}"
            )
    default_result = validate_configuration(_DEFAULT_CONFIGURATION)
    if not default_result.is_valid:
        raise RuntimeError("catálogo inválido: configuração inicial incompatível")


_validate_catalog_definition()
