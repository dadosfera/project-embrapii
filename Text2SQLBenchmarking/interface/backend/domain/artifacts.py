"""Contratos dos artefatos Parquet produzidos pelo pipeline batch."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata

import pandas as pd

from interface.backend.adapters.metric_contract import ADDITIONAL_METRIC_COLUMNS


GENERATION_COLUMNS = (
    "id",
    "question",
    "sql_ground_truth",
    "sql_generated",
    "tempo_geracao",
)

EXECUTION_OPERATIONAL_COLUMNS = (
    "tempo_execucao_ground_truth",
    "execucao_correta_ground_truth",
    "tempo_execucao_generated",
    "execucao_correta_generated",
    "erro_execucao_generated",
    "execucoes_iguais",
)

EXECUTION_COLUMNS = EXECUTION_OPERATIONAL_COLUMNS + ADDITIONAL_METRIC_COLUMNS

TIME_COLUMNS = (
    "tempo_geracao",
    "tempo_execucao_ground_truth",
    "tempo_execucao_generated",
)


class ArtifactKind(str, Enum):
    """Estágio científico representado pelo arquivo."""

    GENERATION = "generation"
    EXECUTED = "executed"


class InvalidArtifactCode(str, Enum):
    """Código estável que poderá ser mapeado pela futura API."""

    INVALID_PARQUET = "INVALID_PARQUET"


@dataclass(frozen=True)
class ArtifactColumn:
    """Metadados previsíveis de uma coluna persistida."""

    name: str
    physical_type: str
    null_count: int


@dataclass(frozen=True)
class ArtifactMetadata:
    """Metadados validados, sem paths ou conteúdo das linhas."""

    kind: ArtifactKind
    row_count: int
    columns: tuple[ArtifactColumn, ...]
    additional_columns: tuple[str, ...]

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)


@dataclass(frozen=True)
class ParquetArtifact:
    """DataFrame lido junto de seu contrato validado."""

    metadata: ArtifactMetadata
    dataframe: pd.DataFrame


class ArtifactValidationError(Exception):
    """Falha estruturada, segura para futura tradução em ``INVALID_PARQUET``."""

    public_message = "O arquivo Parquet é inválido ou incompatível."

    def __init__(self, internal_detail: str) -> None:
        super().__init__(self.public_message)
        self.code = InvalidArtifactCode.INVALID_PARQUET
        self.internal_detail = internal_detail


_TIMEOUT_PATTERN = re.compile(
    r"erro: a query excedeu o tempo limite de [0-9]+(?:\.[0-9]+)? segundos\."
)


def normalize_timeout_message(message: str) -> str:
    """Normaliza texto sem ampliar o padrão histórico reconhecido."""

    normalized = unicodedata.normalize("NFKC", message).casefold().strip()
    return " ".join(normalized.split())


def is_historical_timeout(message: object) -> bool:
    """Reconhece somente a frase completa confirmada nos artefatos atuais."""

    if not isinstance(message, str):
        return False
    return _TIMEOUT_PATTERN.fullmatch(normalize_timeout_message(message)) is not None
