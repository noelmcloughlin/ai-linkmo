"""Fixtures for the project's tests: the exposure, the command tree, the app and its contract."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from ai_risk_ontology_linkmo.cli import build_cli
from ai_risk_ontology_linkmo.exposure import load_exposure


@pytest.fixture(scope="session")
def exposure():
    return load_exposure()


@pytest.fixture(scope="session")
def cli(exposure):
    return build_cli(exposure)


@pytest.fixture(scope="session")
def client():
    from ai_risk_ontology_linkmo.server import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def contract(client):
    return client.get("/openapi.json").json()


@pytest.fixture
def runner():
    return CliRunner()
