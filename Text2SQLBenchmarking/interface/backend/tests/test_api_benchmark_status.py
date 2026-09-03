from __future__ import annotations

import hashlib

import pandas as pd
from fastapi.testclient import TestClient

from interface.backend.api.app import create_app
from interface.backend.benchmark.artifacts import BenchmarkIdentity
from interface.backend.tests.adapter_support import configuration
from interface.backend.tests.conftest import EXECUTION_DATA, GENERATION_DATA
from interface.backend.tests.test_api_health import api_container
from src.metric_contract import ADDITIONAL_METRIC_CONTRACTS, ADDITIONAL_METRIC_COLUMNS


def _params(seed: int = 42, **changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "database": "sih_database",
        "library": "raw_model",
        "model_id": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "context": "default",
        "seed": seed,
    }
    value.update(changes)
    return value


def _write(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    types = {
        "id": "int64",
        "question": "string",
        "sql_ground_truth": "string",
        "sql_generated": "string",
        "tempo_geracao": "float64",
    }
    if "execucoes_iguais" in data:
        types.update(
            {
                "tempo_execucao_ground_truth": "float64",
                "execucao_correta_ground_truth": "boolean",
                "tempo_execucao_generated": "float64",
                "execucao_correta_generated": "boolean",
                "erro_execucao_generated": "string",
                "execucoes_iguais": "boolean",
            }
        )
    pd.DataFrame(data).astype(types).to_parquet(path, index=False)


def _paths(container):
    identity = BenchmarkIdentity.create(configuration(), 42)
    return container.artifacts.paths_for(identity)


def test_status_not_started_creates_no_job_and_does_not_acquire_operation(tmp_path, monkeypatch):
    container = api_container(tmp_path)

    def forbidden(_):
        raise AssertionError("consulta read-only não deve adquirir operação")

    with TestClient(create_app(container=container)) as client:
        original = container.coordinator.try_acquire
        monkeypatch.setattr(container.coordinator, "try_acquire", forbidden)
        response = client.get("/api/v1/benchmark/experiments/status", params=_params())
        monkeypatch.setattr(container.coordinator, "try_acquire", original)

    assert response.status_code == 200
    assert response.json()["artifact_state"] == "not_started"
    assert response.json()["metrics"] is None
    assert response.json()["counts"] is None
    assert response.json()["times"] is None
    assert container.journal.latest() is None
    assert not container.coordinator.status().is_busy
    assert not container.artifacts.resources_root.exists()


def test_raw_examples_status_is_independent_and_uses_its_artifact_token(tmp_path):
    container = api_container(tmp_path)

    with TestClient(create_app(container=container)) as client:
        response = client.get(
            "/api/v1/benchmark/experiments/status",
            params=_params(context="examples"),
        )

    body = response.json()
    assert response.status_code == 200
    assert body["configuration"]["context"] == "examples"
    assert body["artifact_state"] == "not_started"
    assert body["generation"]["relative_path"].endswith(
        "queries_geradas_rawModel_exemplos_42.parquet"
    )
    assert body["execution"]["relative_path"].endswith(
        "queries_geradas_rawModel_exemplos_42_executado.parquet"
    )


def test_status_generation_only_exposes_relative_snapshots(tmp_path):
    container = api_container(tmp_path)
    paths = _paths(container)
    _write(paths.generation, GENERATION_DATA)

    with TestClient(create_app(container=container)) as client:
        response = client.get("/api/v1/benchmark/experiments/status", params=_params())

    body = response.json()
    assert body["artifact_state"] == "generation_only"
    assert body["generation"]["exists"] is True
    assert body["execution"]["exists"] is False
    assert body["generation"]["relative_path"].startswith("sih_database/")
    assert body["metrics"] is None and body["counts"] is None and body["times"] is None


def test_status_complete_calculates_aggregates_without_altering_artifacts(tmp_path):
    container = api_container(tmp_path)
    paths = _paths(container)
    executed = {
        key: list(value) for key, value in EXECUTION_DATA.items()
    }
    for key in executed:
        executed[key] = executed[key] * 2
    executed["id"] = [1, 2]
    executed["execucoes_iguais"] = [True, False]
    executed["tempo_geracao"] = [1.0, 4.0]
    executed["tempo_execucao_ground_truth"] = [2.0, 5.0]
    executed["tempo_execucao_generated"] = [3.0, 6.0]
    _write(paths.generation, GENERATION_DATA)
    _write(paths.execution, executed)
    before = {
        path: (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        for path in (paths.generation, paths.execution)
    }

    with TestClient(create_app(container=container)) as client:
        response = client.get("/api/v1/benchmark/experiments/status", params=_params())

    body = response.json()
    assert body["artifact_state"] == "complete"
    assert body["configuration"] == {
        "database": "sih_database",
        "library": "raw_model",
        "model_id": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "context": "default",
    }
    assert body["metrics"]["execution_accuracy"] == {
        "value": 0.5,
        "available": True,
        "numerator": 1,
        "denominator": 2,
    }
    assert len(body["metrics"]) == 13
    for contract in ADDITIONAL_METRIC_CONTRACTS:
        assert body["metrics"][contract.key] == {
            "value": 1.0,
            "available": True,
            "denominator": 2,
        }
    assert body["counts"] == {
        "total": 2,
        "correct": 1,
        "incorrect_without_error": 1,
        "errors": 0,
        "timeouts": 0,
    }
    assert body["times"] == {
        "generation": 5.0,
        "execution_ground_truth": 7.0,
        "execution_generated": 9.0,
        "execution_total": 16.0,
        "recorded_total": 21.0,
    }
    after = {
        path: (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        for path in (paths.generation, paths.execution)
    }
    assert after == before


def test_status_reports_invalid_structural_or_semantic_results_safely(tmp_path):
    container = api_container(tmp_path)
    paths = _paths(container)
    _write(paths.execution, EXECUTION_DATA)

    with TestClient(create_app(container=container)) as client:
        structural = client.get("/api/v1/benchmark/experiments/status", params=_params())

    assert structural.json()["artifact_state"] == "invalid_result"
    assert structural.json()["invalid_reason"] == "execução sem geração"
    assert structural.json()["metrics"] is None

    _write(paths.generation, GENERATION_DATA)
    invalid_flags = {key: list(value) for key, value in EXECUTION_DATA.items()}
    invalid_flags["execucao_correta_generated"] = [False]
    invalid_flags["execucoes_iguais"] = [True]
    _write(paths.execution, invalid_flags)
    with TestClient(create_app(container=container)) as client:
        semantic = client.get("/api/v1/benchmark/experiments/status", params=_params())

    assert semantic.json()["artifact_state"] == "invalid_result"
    assert semantic.json()["invalid_reason"] == (
        "O resultado executado tem dados semanticamente inconsistentes."
    )
    assert semantic.json()["metrics"] is None
    assert semantic.json()["counts"] is None
    assert semantic.json()["times"] is None


def test_status_marks_legacy_executed_artifact_without_metrics_invalid(tmp_path):
    container = api_container(tmp_path)
    paths = _paths(container)
    _write(paths.generation, GENERATION_DATA)
    legacy = {
        key: value
        for key, value in EXECUTION_DATA.items()
        if key not in ADDITIONAL_METRIC_COLUMNS
    }
    _write(paths.execution, legacy)

    with TestClient(create_app(container=container)) as client:
        response = client.get(
            "/api/v1/benchmark/experiments/status",
            params=_params(),
        )

    body = response.json()
    assert body["artifact_state"] == "invalid_result"
    assert body["metrics"] is None


def test_status_rejects_incompatible_configuration(tmp_path):
    with TestClient(create_app(container=api_container(tmp_path))) as client:
        response = client.get(
            "/api/v1/benchmark/experiments/status",
            params=_params(library="xiyan_sql"),
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_COMBINATION"
