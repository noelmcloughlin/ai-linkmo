"""The API kernel serves every exposed class from the schema and keeps the hand paths.

These tests run the real app in a test client, so the lifespan registers the endpoints and
loads the ontology once for the module. The expected counts were verified against
ai-atlas-nexus 1.2.5 by ``test_exposure.py``.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from lib.api.exposure import load_exposure


@pytest.fixture(scope="module")
def client():
    from lib.api.server import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def openapi(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


def test_contract_lists_every_class_and_hand_path(openapi):
    exposure = load_exposure()
    for exposed in exposure.classes.values():
        operation = openapi["paths"][exposed.path]["get"]
        assert operation["operationId"] == exposed.operation_id
        assert operation["summary"] == f"List {exposed.name}"
    for path, methods in exposure.hand_paths.items():
        for method, operation in methods.items():
            assert openapi["paths"][path][method]["operationId"] == operation["operationId"]
    # The upload keeps the security scheme the overlay declares.
    assert openapi["paths"]["/byo"]["put"]["security"] == [{"ApiKeyAuth": []}]
    assert "ApiKeyAuth" in openapi["components"]["securitySchemes"]


def test_contract_carries_the_models(openapi):
    schemas = openapi["components"]["schemas"]
    assert "Risk" in schemas
    assert "Envelope_Risk" in schemas
    assert set(schemas["Envelope_Risk"]["properties"]) == {
        "items",
        "count",
        "validation_errors",
        "item",
    }
    # An enum slot lists its values as the parameter's choices.
    adapter_type = next(
        p for p in openapi["paths"]["/adapter"]["get"]["parameters"] if p["name"] == "hasAdapterType"
    )
    enum = adapter_type["schema"].get("enum") or next(
        option["enum"] for option in adapter_type["schema"]["anyOf"] if "enum" in option
    )
    assert "LORA" in enum


def test_enum_filter_rejects_a_value_outside_the_enum(client):
    assert client.get("/adapter", params={"hasAdapterType": "NOPE"}).status_code == 422
    response = client.get("/adapter", params={"hasAdapterType": "LORA"})
    assert response.status_code == 200
    assert response.json()["count"] == 19


def test_listing_returns_the_envelope(client):
    response = client.get("/risk", params={"isDefinedByTaxonomy": "nist-ai-rmf"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "count", "validation_errors"}
    assert body["count"] == 12 and len(body["items"]) == 12


def test_lookup_by_id_returns_the_item(client):
    response = client.get("/taxonomy", params={"id": "nist-ai-rmf"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"item"}
    assert body["item"]["id"] == "nist-ai-rmf"


def test_related_lookup(client):
    response = client.get(
        "/control", params={"hasRelatedRisk": "atlas-toxic-output", "related": "true"}
    )
    assert response.status_code == 200
    assert response.json()["count"] == 4


def test_unknown_query_parameter_is_ignored(client):
    # FastAPI drops a query parameter the signature does not declare, so a name the schema
    # does not know never reaches the handler and the listing is simply unfiltered.
    response = client.get("/taxonomy", params={"nosuchslot": "x"})
    assert response.status_code == 200
    assert response.json()["count"] == client.get("/taxonomy").json()["count"]


def test_hand_paths_keep_their_behaviour(client):
    assert client.get("/graph").status_code == 200
    schemaview = client.get("/schemaview")
    assert schemaview.status_code == 200
    assert schemaview.json()["counts"]["classes"] > 0
    assert client.put("/byo", params={"filename": "../x"}, content=b"a: 1\n").status_code == 400
    assert client.get("/classes").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}
