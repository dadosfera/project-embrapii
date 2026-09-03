from fastapi.testclient import TestClient

from interface.backend.api.app import create_app
from interface.backend.tests.test_api_health import api_container


def test_catalog_exposes_public_ids_and_no_internal_tokens(tmp_path):
    with TestClient(create_app(container=api_container(tmp_path))) as client:
        response = client.get("/api/v1/catalog")
        openapi = client.get("/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    assert payload["initial_configuration"]["library"] == "raw_model"
    assert {item["id"] for item in payload["databases"]} == {"sih_database", "datasus"}
    assert len(payload["models"]) == 10
    assert payload["libraries"][2]["availability"]["chat"]["available"] is False
    raw_model = next(item for item in payload["libraries"] if item["id"] == "raw_model")
    assert raw_model["contexts"] == ["default", "examples"]
    assert raw_model["availability"]["chat"]["available"] is True
    assert raw_model["availability"]["benchmark"]["available"] is True
    metrics = payload["metrics"]
    assert len(metrics) == 13
    assert {item["key"] for item in metrics} == {
        "execution_accuracy",
        "soft_f1",
        "stats",
        "similarity",
        "ves",
        "exact_match",
        "component_match",
        "structural_correctness",
        "logical_form_accuracy",
        "leco",
        "skeleton_correctness",
        "pcm_f1",
        "query_affinity_score",
    }
    assert {
        item["code"] for item in metrics if item["initially_visible"]
    } == {"EX", "CM", "Soft_F1"}
    assert next(item for item in metrics if item["code"] == "EX")[
        "prominence"
    ] == "primary"
    assert next(item for item in metrics if item["key"] == "soft_f1")[
        "label"
    ] == "Soft F1"
    assert next(item for item in metrics if item["key"] == "component_match")[
        "label"
    ] == "Component Match (CM)"
    assert all(item["format"] == "percentage" for item in metrics)
    serialized = str(payload).lower()
    for forbidden in ("legacy_token", "registry_name", "fingerprint", "hf_token", "local_models"):
        assert forbidden not in serialized
    assert "legacy_token" not in str(openapi.json()).lower()
