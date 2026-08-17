"""Taxonomia pública e classificadores conservadores de falhas da interface."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import errno
import re
import socket
from typing import Iterable, Iterator


class PublicErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNSUPPORTED_COMBINATION = "UNSUPPORTED_COMBINATION"
    RESOURCE_BUSY = "RESOURCE_BUSY"
    MODEL_LOAD_ERROR = "MODEL_LOAD_ERROR"
    SQL_GENERATION_ERROR = "SQL_GENERATION_ERROR"
    UNSAFE_SQL = "UNSAFE_SQL"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    SQL_SYNTAX_ERROR = "SQL_SYNTAX_ERROR"
    QUERY_TIMEOUT = "QUERY_TIMEOUT"
    QUERY_EXECUTION_ERROR = "QUERY_EXECUTION_ERROR"
    ARTIFACT_NOT_FOUND = "ARTIFACT_NOT_FOUND"
    INVALID_PARQUET = "INVALID_PARQUET"
    REEXECUTION_CONFIRMATION_REQUIRED = "REEXECUTION_CONFIRMATION_REQUIRED"
    REEXECUTION_STATE_CHANGED = "REEXECUTION_STATE_CHANGED"
    ARCHIVE_ERROR = "ARCHIVE_ERROR"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # Códigos legítimos do catálogo já publicados antes da Fase 11.
    UNKNOWN_DATABASE = "UNKNOWN_DATABASE"
    UNKNOWN_LIBRARY = "UNKNOWN_LIBRARY"
    UNKNOWN_MODEL = "UNKNOWN_MODEL"
    UNKNOWN_CONTEXT = "UNKNOWN_CONTEXT"


@dataclass(frozen=True)
class PublicErrorDefinition:
    fallback_message: str
    retryable: bool
    http_status: int


PUBLIC_ERROR_DEFINITIONS: dict[PublicErrorCode, PublicErrorDefinition] = {
    PublicErrorCode.INVALID_REQUEST: PublicErrorDefinition("A requisição informada não é válida.", False, 422),
    PublicErrorCode.UNSUPPORTED_COMBINATION: PublicErrorDefinition("A configuração selecionada não é suportada.", False, 400),
    PublicErrorCode.RESOURCE_BUSY: PublicErrorDefinition("Outra operação pesada está em andamento. Tente novamente após a conclusão.", True, 409),
    PublicErrorCode.MODEL_LOAD_ERROR: PublicErrorDefinition("Não foi possível baixar ou carregar o modelo selecionado.", True, 500),
    PublicErrorCode.SQL_GENERATION_ERROR: PublicErrorDefinition("Não foi possível gerar uma consulta SQL válida.", True, 500),
    PublicErrorCode.UNSAFE_SQL: PublicErrorDefinition("A consulta gerada não atende à política de somente leitura.", False, 400),
    PublicErrorCode.DATABASE_CONNECTION_ERROR: PublicErrorDefinition("Não foi possível conectar ao banco de dados.", True, 503),
    PublicErrorCode.SQL_SYNTAX_ERROR: PublicErrorDefinition("A consulta gerada possui erro de sintaxe.", False, 400),
    PublicErrorCode.QUERY_TIMEOUT: PublicErrorDefinition("A consulta excedeu o tempo limite.", True, 504),
    PublicErrorCode.QUERY_EXECUTION_ERROR: PublicErrorDefinition("Não foi possível executar a consulta no banco.", True, 500),
    PublicErrorCode.ARTIFACT_NOT_FOUND: PublicErrorDefinition("O artefato esperado não foi encontrado.", False, 404),
    PublicErrorCode.INVALID_PARQUET: PublicErrorDefinition("O resultado existente é inválido e não será sobrescrito automaticamente.", False, 400),
    PublicErrorCode.REEXECUTION_CONFIRMATION_REQUIRED: PublicErrorDefinition("Confirme explicitamente a reexecução antes de iniciar o Benchmark.", False, 409),
    PublicErrorCode.REEXECUTION_STATE_CHANGED: PublicErrorDefinition("Os artefatos mudaram desde a confirmação. Confirme a reexecução novamente.", False, 409),
    PublicErrorCode.ARCHIVE_ERROR: PublicErrorDefinition("Não foi possível arquivar os artefatos existentes com segurança.", False, 500),
    PublicErrorCode.JOB_NOT_FOUND: PublicErrorDefinition("O job solicitado não existe.", False, 404),
    PublicErrorCode.INTERNAL_ERROR: PublicErrorDefinition("Ocorreu um erro interno. Nenhum detalhe interno foi exposto.", False, 500),
    PublicErrorCode.UNKNOWN_DATABASE: PublicErrorDefinition("A base de dados selecionada não existe.", False, 400),
    PublicErrorCode.UNKNOWN_LIBRARY: PublicErrorDefinition("A biblioteca selecionada não existe.", False, 400),
    PublicErrorCode.UNKNOWN_MODEL: PublicErrorDefinition("O modelo selecionado não existe.", False, 400),
    PublicErrorCode.UNKNOWN_CONTEXT: PublicErrorDefinition("O contexto selecionado não existe.", False, 400),
}


@dataclass(frozen=True)
class PublicErrorPayload:
    code: PublicErrorCode
    message: str
    retryable: bool

    def as_dict(self) -> dict[str, str | bool]:
        return {"code": self.code.value, "message": self.message, "retryable": self.retryable}


def public_error(
    code: PublicErrorCode | str,
    message: str | None = None,
    retryable: bool | None = None,
) -> PublicErrorPayload:
    """Constrói apenas payloads catalogados; código desconhecido cai em INTERNAL_ERROR."""

    try:
        selected = code if isinstance(code, PublicErrorCode) else PublicErrorCode(code)
    except ValueError:
        selected = PublicErrorCode.INTERNAL_ERROR
        message = None
        retryable = None
    definition = PUBLIC_ERROR_DEFINITIONS[selected]
    return PublicErrorPayload(
        selected,
        message or definition.fallback_message,
        definition.retryable if retryable is None else retryable,
    )


def http_status_for(code: PublicErrorCode | str) -> int:
    return PUBLIC_ERROR_DEFINITIONS[public_error(code).code].http_status


def iter_exception_chain(exception: BaseException, *, max_depth: int = 24) -> Iterator[BaseException]:
    """Segue a cadeia exibida pelo Python, com limite e proteção contra ciclos."""

    current: BaseException | None = exception
    seen: set[int] = set()
    while current is not None and len(seen) < max_depth:
        marker = id(current)
        if marker in seen:
            break
        seen.add(marker)
        yield current
        if isinstance(current.__cause__, BaseException):
            current = current.__cause__
        elif not current.__suppress_context__ and isinstance(current.__context__, BaseException):
            current = current.__context__
        else:
            current = None


class ModelLoadCause(str, Enum):
    DISK_FULL = "disk_full"
    CUDA_OOM = "cuda_oom"
    NETWORK = "network"
    MODEL_UNAVAILABLE = "model_unavailable"
    GENERIC = "generic"


@dataclass(frozen=True)
class ModelLoadClassification:
    cause: ModelLoadCause
    error: PublicErrorPayload


_DISK_FULL_TEXT = re.compile(r"\bno space left on device\b", re.IGNORECASE)
_CUDA_OOM_TEXT = re.compile(
    r"(?:\bcuda out of memory\b|\bout of memory on (?:cuda|gpu)\b|torch\.cuda\.outofmemoryerror)",
    re.IGNORECASE,
)
_NETWORK_TEXT = re.compile(
    r"(?:temporary failure in name resolution|name or service not known|"
    r"failed to establish a new connection|connection (?:timed out|refused)|"
    r"network is unreachable|connect timeout|read timeout while downloading)",
    re.IGNORECASE,
)
_MODEL_UNAVAILABLE_TEXT = re.compile(
    r"(?:repositorynotfounderror|gatedrepoerror|revisionnotfounderror|"
    r"repository not found|gated repo|model .* (?:not found|is gated|is restricted)|"
    r"access to .*model.*(?:denied|restricted)|localentrynotfounderror)",
    re.IGNORECASE,
)
_MODEL_LOADING_TEXT = re.compile(
    r"(?:snapshot_download|from_pretrained|huggingface_hub(?:\.|/)file_download|"
    r"(?:baixando|carregando|loading|downloading) (?:o |the )?model(?:o)?(?: para| from|$))",
    re.IGNORECASE,
)


def _exception_texts(exception: BaseException, extra_text: Iterable[object] = ()) -> tuple[str, ...]:
    values: list[str] = []
    for current in iter_exception_chain(exception):
        values.append(str(current))
        for attribute in ("stderr", "stdout", "output"):
            value = getattr(current, attribute, None)
            if isinstance(value, (str, bytes)):
                values.append(value.decode("utf-8", "replace") if isinstance(value, bytes) else value)
    values.extend(str(value) for value in extra_text if value is not None)
    return tuple(values)


def _module_in_family(module: str, *families: str) -> bool:
    normalized = module.lower()
    return any(normalized == family or normalized.startswith(f"{family}.") for family in families)


def _is_cuda_oom_type(exception: BaseException) -> bool:
    exception_type = type(exception)
    return (
        exception_type.__name__ == "OutOfMemoryError"
        and _module_in_family(exception_type.__module__, "torch")
    )


def _is_network_type(exception: BaseException) -> bool:
    if isinstance(exception, (ConnectionError, TimeoutError, socket.gaierror)):
        return True
    exception_type = type(exception)
    module = exception_type.__module__.lower()
    name = exception_type.__name__.lower()
    return (
        _module_in_family(module, "requests", "urllib3", "httpx", "httpcore")
        and any(marker in name for marker in ("connection", "timeout", "network", "dns"))
    )


def _is_model_unavailable_type(exception: BaseException) -> bool:
    exception_type = type(exception)
    return _module_in_family(exception_type.__module__, "huggingface_hub") and exception_type.__name__ in {
        "RepositoryNotFoundError",
        "GatedRepoError",
        "EntryNotFoundError",
        "LocalEntryNotFoundError",
        "RevisionNotFoundError",
    }


def _has_model_loading_provenance(
    exception: BaseException,
    extra_text: Iterable[object] = (),
) -> bool:
    chain = tuple(iter_exception_chain(exception))
    if any(
        _module_in_family(type(item).__module__, "huggingface_hub.file_download")
        for item in chain
    ):
        return True
    return any(_MODEL_LOADING_TEXT.search(text) for text in _exception_texts(exception, extra_text))


def classify_model_load_error(
    exception: BaseException,
    *,
    extra_text: Iterable[object] = (),
) -> ModelLoadClassification:
    """Classifica somente evidências fortes; mensagens públicas nunca usam texto bruto."""

    chain = tuple(iter_exception_chain(exception))
    texts = _exception_texts(exception, extra_text)

    if any(isinstance(item, OSError) and item.errno == errno.ENOSPC for item in chain) or any(
        _DISK_FULL_TEXT.search(text) for text in texts
    ):
        return ModelLoadClassification(
            ModelLoadCause.DISK_FULL,
            public_error(
                PublicErrorCode.MODEL_LOAD_ERROR,
                "Não há espaço suficiente em disco para baixar ou carregar este modelo. Libere espaço no servidor e tente novamente.",
                True,
            ),
        )
    if any(_is_cuda_oom_type(item) for item in chain) or any(_CUDA_OOM_TEXT.search(text) for text in texts):
        return ModelLoadClassification(
            ModelLoadCause.CUDA_OOM,
            public_error(
                PublicErrorCode.MODEL_LOAD_ERROR,
                "Não há memória suficiente na GPU para carregar este modelo.",
                True,
            ),
        )
    if any(_is_network_type(item) for item in chain) or any(_NETWORK_TEXT.search(text) for text in texts):
        return ModelLoadClassification(
            ModelLoadCause.NETWORK,
            public_error(
                PublicErrorCode.MODEL_LOAD_ERROR,
                "Não foi possível baixar o modelo por uma falha de rede. Verifique a conectividade do servidor e tente novamente.",
                True,
            ),
        )
    if any(_is_model_unavailable_type(item) for item in chain) or any(
        _MODEL_UNAVAILABLE_TEXT.search(text) for text in texts
    ):
        return ModelLoadClassification(
            ModelLoadCause.MODEL_UNAVAILABLE,
            public_error(
                PublicErrorCode.MODEL_LOAD_ERROR,
                "O modelo não está disponível ou o acesso a ele não foi autorizado.",
                False,
            ),
        )
    return ModelLoadClassification(
        ModelLoadCause.GENERIC,
        public_error(PublicErrorCode.MODEL_LOAD_ERROR),
    )


def _sqlstate(exception: BaseException) -> str | None:
    for current in iter_exception_chain(exception):
        for value in (
            getattr(current, "sqlstate", None),
            getattr(current, "pgcode", None),
            getattr(getattr(current, "diag", None), "sqlstate", None),
        ):
            if isinstance(value, str) and len(value) == 5:
                return value.upper()
    return None


_QUERY_TIMEOUT_TEXT = re.compile(
    r"(?:canceling statement due to statement timeout|query canceled due to statement timeout|query excedeu o tempo limite)",
    re.IGNORECASE,
)
_SQL_SYNTAX_TEXT = re.compile(
    r"(?:syntax error at or near|unterminated quoted string|unterminated dollar-quoted string)",
    re.IGNORECASE,
)
_DATABASE_CONNECTION_TEXT = re.compile(
    r"(?:could not connect to server|connection to server .* failed|server closed the connection unexpectedly|"
    r"connection refused.*(?:postgres|database|server)|database system is starting up|"
    r"\bsqlstate(?:\s*[:=]?\s*|\s*\[\s*)08[0-9a-z]{3}(?:\s*\])?)",
    re.IGNORECASE,
)


def _is_database_connection_type(exception: BaseException) -> bool:
    exception_type = type(exception)
    module = exception_type.__module__.lower()
    name = exception_type.__name__
    if _module_in_family(module, "psycopg", "psycopg2"):
        return name in {"OperationalError", "InterfaceError"} or "Connection" in name
    if _module_in_family(module, "asyncpg"):
        return "Connection" in name or name in {"CannotConnectNowError"}
    if _module_in_family(module, "sqlalchemy"):
        return (
            name in {"DisconnectionError", "InvalidatePoolError", "TimeoutError"}
            or getattr(exception, "connection_invalidated", False) is True
        )
    return False


def _has_database_connection_evidence(exception: BaseException) -> bool:
    state = _sqlstate(exception)
    if state is not None and state.startswith("08"):
        return True
    chain = tuple(iter_exception_chain(exception))
    return any(_is_database_connection_type(item) for item in chain) or any(
        _DATABASE_CONNECTION_TEXT.search(text) for text in _exception_texts(exception)
    )


def _is_query_canceled_type(exception: BaseException) -> bool:
    exception_type = type(exception)
    return (
        exception_type.__name__ in {"QueryCanceled", "QueryCanceledError"}
        and _module_in_family(exception_type.__module__, "psycopg", "psycopg2", "asyncpg")
    )


def classify_loading_model_error(exception: BaseException) -> PublicErrorPayload:
    """Classifica o estágio amplo de setup sem confundir banco com aquisição de modelo."""

    if _has_database_connection_evidence(exception):
        return public_error(PublicErrorCode.DATABASE_CONNECTION_ERROR)

    classified = classify_model_load_error(exception)
    if classified.cause is ModelLoadCause.NETWORK and not _has_model_loading_provenance(exception):
        return public_error(PublicErrorCode.INTERNAL_ERROR)
    return classified.error


def classify_query_execution_error(exception: BaseException) -> PublicErrorPayload:
    """Usa SQLSTATE/tipos antes de padrões textuais específicos."""

    state = _sqlstate(exception)
    if state == "57014":
        return public_error(PublicErrorCode.QUERY_TIMEOUT)
    if state == "42601":
        return public_error(PublicErrorCode.SQL_SYNTAX_ERROR)
    if state is not None and state.startswith("08"):
        return public_error(PublicErrorCode.DATABASE_CONNECTION_ERROR)

    chain = tuple(iter_exception_chain(exception))
    texts = _exception_texts(exception)
    if any(_is_query_canceled_type(item) for item in chain) or any(
        _QUERY_TIMEOUT_TEXT.search(text) for text in texts
    ):
        return public_error(PublicErrorCode.QUERY_TIMEOUT)
    if any(
        type(item).__name__ == "SyntaxError"
        and _module_in_family(type(item).__module__, "psycopg", "psycopg2", "asyncpg")
        for item in chain
    ) or any(_SQL_SYNTAX_TEXT.search(text) for text in texts):
        return public_error(PublicErrorCode.SQL_SYNTAX_ERROR)
    if any(_is_network_type(item) for item in chain) or any(
        _DATABASE_CONNECTION_TEXT.search(text) for text in texts
    ):
        return public_error(PublicErrorCode.DATABASE_CONNECTION_ERROR)
    return public_error(PublicErrorCode.QUERY_EXECUTION_ERROR)


def classify_generation_subprocess_error(exception: BaseException) -> PublicErrorPayload:
    """Classifica geração sem inferir em qual etapa interna o subprocesso falhou."""

    if _has_database_connection_evidence(exception):
        return public_error(PublicErrorCode.DATABASE_CONNECTION_ERROR)

    classified = classify_model_load_error(exception)
    loading_provenance = _has_model_loading_provenance(exception)
    if classified.cause is ModelLoadCause.MODEL_UNAVAILABLE:
        return classified.error
    if classified.cause is ModelLoadCause.DISK_FULL:
        if loading_provenance:
            return classified.error
        return public_error(
            PublicErrorCode.SQL_GENERATION_ERROR,
            "Não há espaço suficiente em disco para concluir a geração do Benchmark. Libere espaço no servidor e tente novamente.",
            True,
        )
    if classified.cause is ModelLoadCause.CUDA_OOM:
        if loading_provenance:
            return classified.error
        return public_error(
            PublicErrorCode.SQL_GENERATION_ERROR,
            "Não há memória suficiente na GPU para concluir a geração do Benchmark.",
            True,
        )
    if classified.cause is ModelLoadCause.NETWORK and loading_provenance:
        return classified.error
    return public_error(PublicErrorCode.SQL_GENERATION_ERROR)


def classify_execution_subprocess_error(exception: BaseException) -> PublicErrorPayload:
    return classify_query_execution_error(exception)
