from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.metric_contract import ADDITIONAL_METRIC_COLUMNS


GENERATION_DATA: dict[str, list[Any]] = {
    "id": [1],
    "question": ["Pergunta sintética"],
    "sql_ground_truth": ["SELECT 1"],
    "sql_generated": ["SELECT 1"],
    "tempo_geracao": [0.25],
}

EXECUTION_DATA: dict[str, list[Any]] = {
    **GENERATION_DATA,
    "tempo_execucao_ground_truth": [0.01],
    "execucao_correta_ground_truth": [True],
    "tempo_execucao_generated": [0.02],
    "execucao_correta_generated": [True],
    "erro_execucao_generated": [None],
    "execucoes_iguais": [True],
    **{column: [1.0] for column in ADDITIONAL_METRIC_COLUMNS},
}


@pytest.fixture
def parquet_factory(tmp_path: Path):
    def factory(
        *,
        executed: bool = False,
        textual_id: bool = False,
        empty: bool = False,
        changes: dict[str, list[Any]] | None = None,
        extra_columns: dict[str, list[Any]] | None = None,
        name: str = "artifact.parquet",
    ) -> Path:
        source = EXECUTION_DATA if executed else GENERATION_DATA
        data = {column: list(values) for column, values in source.items()}
        if textual_id:
            data["id"] = ["synthetic-id"]
        if changes:
            data.update(changes)
        if extra_columns:
            data.update(extra_columns)

        frame = pd.DataFrame(data)
        frame = frame.astype(
            {
                "id": "string" if textual_id else "int64",
                "question": "string",
                "sql_ground_truth": "string",
                "sql_generated": "string",
                "tempo_geracao": "float64",
                **(
                    {
                        "tempo_execucao_ground_truth": "float64",
                        "execucao_correta_ground_truth": "boolean",
                        "tempo_execucao_generated": "float64",
                        "execucao_correta_generated": "boolean",
                        "erro_execucao_generated": "string",
                        "execucoes_iguais": "boolean",
                        **{
                            column: "Float64"
                            for column in ADDITIONAL_METRIC_COLUMNS
                        },
                    }
                    if executed
                    else {}
                ),
            }
        )
        if empty:
            frame = frame.iloc[0:0]
        path = tmp_path / name
        frame.to_parquet(path, index=False)
        return path

    return factory
