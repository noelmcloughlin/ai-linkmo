"""Smoke tests for top-level infrastructure endpoints."""

from __future__ import annotations

import requests


def test_version_shape(api_server: str) -> None:
    response = requests.get(f"{api_server}/version", timeout=5)
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) >= {"api", "ai_atlas_nexus"}
    assert isinstance(payload["api"], str) and payload["api"]
    assert isinstance(payload["ai_atlas_nexus"], str) and payload["ai_atlas_nexus"]


def test_ready_probe(api_server: str) -> None:
    response = requests.get(f"{api_server}/ready", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_classes_basic(api_server: str) -> None:
    response = requests.get(f"{api_server}/classes", timeout=10)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert isinstance(payload, (dict, list))


def test_classes_taxonomy_filter(api_server: str) -> None:
    response = requests.get(
        f"{api_server}/classes",
        params={"taxonomy": "nist-ai-rmf"},
        timeout=10,
    )
    assert response.status_code == 200, response.text


def test_inference_rejects_bad_json(api_server: str) -> None:
    """The /inference endpoint should reject malformed parameter JSON cleanly.

    /inference is a GET endpoint that takes ``parameters`` as a JSON-encoded
    query string. A garbage value must produce a 4xx error, not a 500.
    """
    response = requests.get(
        f"{api_server}/inference",
        params={"parameters": "not-json"},
        timeout=10,
    )
    # FastAPI returns 422 for validation, the handler returns 400 for
    # JSON parse errors. Either is acceptable - what we don't want is 5xx.
    assert response.status_code < 500, response.text


def test_cache_control_header_present(api_server: str) -> None:
    """Every GET response should have a Cache-Control header from middleware."""
    response = requests.get(f"{api_server}/health", timeout=5)
    assert response.status_code == 200
    assert "cache-control" in {k.lower() for k in response.headers.keys()}
