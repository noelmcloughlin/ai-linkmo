"""The committed contract is the one the server serves, and the references render.

``docs/openapi.json`` is written by ``just gen-openapi``, which runs the linkmo project's
export script. If the exposure file or the schema changes and the file is not regenerated,
the first test fails and says so.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
PUBLISHED = ROOT / "docs" / "openapi.json"
SCRIPT = ROOT / "ai-risk-ontology-linkmo" / "scripts" / "export_openapi.py"


def test_the_published_contract_is_current():
    spec = importlib.util.spec_from_file_location("linkmo_export_openapi", SCRIPT)
    export = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(export)
    assert PUBLISHED.is_file(), "run `just gen-openapi` to publish the contract"
    assert PUBLISHED.read_text(encoding="utf-8") == export.render(export.build_contract()), (
        "docs/openapi.json is behind the exposure file or the schema; run `just gen-openapi`"
    )


def test_the_published_contract_is_openapi_3_1_with_the_classes():
    contract = json.loads(PUBLISHED.read_text(encoding="utf-8"))
    assert contract["openapi"].startswith("3.1")
    assert "/risk" in contract["paths"] and "/byo" in contract["paths"]
    assert "Risk" in contract["components"]["schemas"]


@pytest.fixture(scope="module")
def client():
    from lib.api.server import app

    with TestClient(app) as test_client:
        yield test_client


def test_the_references_are_served(client):
    for path in ("/docs", "/redoc", "/scalar"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "text/html" in response.headers["content-type"], path
    assert "/openapi.json" in client.get("/scalar").text
    assert client.get("/openapi.json").json() == json.loads(PUBLISHED.read_text(encoding="utf-8"))
