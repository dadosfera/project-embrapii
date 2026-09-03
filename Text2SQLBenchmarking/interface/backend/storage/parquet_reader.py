"""Leitura estrita e sem mutação dos Parquets científicos."""

from __future__ import annotations

import math
from os import PathLike
from pathlib import Path
from typing import Callable

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from interface.backend.domain.artifacts import (
    EXECUTION_COLUMNS,
    GENERATION_COLUMNS,
    TIME_COLUMNS,
    ArtifactColumn,
    ArtifactKind,
    ArtifactMetadata,
    ArtifactValidationError,
    ParquetArtifact,
)
from interface.backend.adapters.metric_contract import ADDITIONAL_METRIC_COLUMNS


_TEXT_COLUMNS = {"question", "sql_ground_truth", "sql_generated", "erro_execucao_generated"}
_BOOLEAN_COLUMNS = {
    "execucao_correta_ground_truth",
    "execucao_correta_generated",
    "execucoes_iguais",
}
_NULLABLE_COLUMNS = {"erro_execucao_generated", *ADDITIONAL_METRIC_COLUMNS}


def _is_text(data_type: pa.DataType) -> bool:
    return pa.types.is_string(data_type) or pa.types.is_large_string(data_type)


def _is_id(data_type: pa.DataType) -> bool:
    return pa.types.is_integer(data_type) or _is_text(data_type)


def _is_numeric(data_type: pa.DataType) -> bool:
    return pa.types.is_integer(data_type) or pa.types.is_floating(data_type)


def _expected_type(column: str) -> tuple[Callable[[pa.DataType], bool], str]:
    if column == "id":
        return _is_id, "inteiro ou texto"
    if column in _TEXT_COLUMNS:
        return _is_text, "texto"
    if column in TIME_COLUMNS:
        return _is_numeric, "numérico"
    if column in ADDITIONAL_METRIC_COLUMNS:
        return _is_numeric, "numérico"
    if column in _BOOLEAN_COLUMNS:
        return pa.types.is_boolean, "booleano"
    raise AssertionError(f"coluna sem contrato interno: {column}")


def _classify(column_names: tuple[str, ...]) -> ArtifactKind:
    names = set(column_names)
    missing_generation = set(GENERATION_COLUMNS) - names
    if missing_generation:
        missing = ", ".join(sorted(missing_generation))
        raise ArtifactValidationError(f"colunas obrigatórias ausentes: {missing}")

    present_execution = set(EXECUTION_COLUMNS) & names
    missing_execution = set(EXECUTION_COLUMNS) - names
    if present_execution and missing_execution:
        missing = ", ".join(sorted(missing_execution))
        raise ArtifactValidationError(f"schema de execução parcial; ausentes: {missing}")
    if not missing_execution:
        return ArtifactKind.EXECUTED
    return ArtifactKind.GENERATION


def _validate_schema(schema: pa.Schema, kind: ArtifactKind) -> None:
    required = GENERATION_COLUMNS + (EXECUTION_COLUMNS if kind is ArtifactKind.EXECUTED else ())
    for column in required:
        data_type = schema.field(column).type
        validator, expected = _expected_type(column)
        if not validator(data_type):
            raise ArtifactValidationError(
                f"tipo incompatível em {column}: {data_type}; esperado {expected}"
            )


def _validate_values(dataframe: pd.DataFrame, kind: ArtifactKind) -> None:
    required = GENERATION_COLUMNS + (EXECUTION_COLUMNS if kind is ArtifactKind.EXECUTED else ())
    for column in required:
        if column not in _NULLABLE_COLUMNS and dataframe[column].isna().any():
            raise ArtifactValidationError(f"valor ausente não permitido em {column}")

    for column in TIME_COLUMNS:
        if column not in dataframe:
            continue
        if any(not math.isfinite(float(value)) for value in dataframe[column]):
            raise ArtifactValidationError(f"valor temporal não finito em {column}")

    if kind is ArtifactKind.EXECUTED:
        ground_truth_failed = dataframe["execucao_correta_ground_truth"] != True  # noqa: E712
        for column in ADDITIONAL_METRIC_COLUMNS:
            missing = dataframe[column].isna()
            if bool((missing != ground_truth_failed).any()):
                raise ArtifactValidationError(
                    f"nulabilidade incompatível com a Ground Truth em {column}"
                )
            if any(
                not math.isfinite(float(value))
                for value in dataframe.loc[~missing, column]
            ):
                raise ArtifactValidationError(f"métrica não finita em {column}")


def read_parquet_artifact(path: str | PathLike[str]) -> ParquetArtifact:
    """Lê e valida um artefato sem alterar o arquivo ou normalizar seus dados."""

    parquet_path = Path(path)
    try:
        parquet_file = pq.ParquetFile(parquet_path)
        table = parquet_file.read()
        schema = table.schema
    except Exception as exc:
        raise ArtifactValidationError(
            f"falha ao abrir Parquet ({type(exc).__name__})"
        ) from exc

    column_names = tuple(schema.names)
    if len(column_names) != len(set(column_names)):
        raise ArtifactValidationError("nomes de colunas duplicados")

    kind = _classify(column_names)
    _validate_schema(schema, kind)

    try:
        dataframe = table.to_pandas()
    except Exception as exc:
        raise ArtifactValidationError(
            f"falha ao materializar Parquet ({type(exc).__name__})"
        ) from exc

    _validate_values(dataframe, kind)
    required = set(GENERATION_COLUMNS)
    if kind is ArtifactKind.EXECUTED:
        required.update(EXECUTION_COLUMNS)

    columns = tuple(
        ArtifactColumn(
            name=name,
            physical_type=str(schema.field(name).type),
            null_count=int(dataframe[name].isna().sum()),
        )
        for name in column_names
    )
    metadata = ArtifactMetadata(
        kind=kind,
        row_count=len(dataframe),
        columns=columns,
        additional_columns=tuple(name for name in column_names if name not in required),
    )
    return ParquetArtifact(metadata=metadata, dataframe=dataframe)
