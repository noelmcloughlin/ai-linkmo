"""The CLI and the API are the same surface.

This replaces the old check that handler signatures matched the hand-written OpenAPI file.
Both kernels now read one exposure, so the thing to prove is that neither drifts from it or
from the other: every scope is an endpoint with the same parameters, and the same question
gets the same answer through the CLI in local mode and through the API.
"""

from __future__ import annotations

import logging

import click
import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from lib.api.exposure import load_exposure
from lib.cli.cli import SHARED_OPTION_NAMES, build_cli


@pytest.fixture(scope="module")
def exposure():
    return load_exposure()


@pytest.fixture(scope="module")
def cli(exposure):
    return build_cli(exposure)


@pytest.fixture(scope="module")
def client():
    from lib.api.server import app

    with TestClient(app) as test_client:
        yield test_client
    # Local mode silences logging for the process; put it back for the tests that follow.
    logging.disable(logging.NOTSET)


@pytest.fixture(scope="module")
def contract(client):
    return client.get("/openapi.json").json()


def _cli_parameters(command: click.Command) -> set[str]:
    """The names a command accepts from the user, the shared CLI options left out."""
    return {p.name for p in command.params} - set(SHARED_OPTION_NAMES)


def _api_parameters(contract, path: str, method: str = "get") -> set[str]:
    operation = contract["paths"][path][method]
    names = {p["name"] for p in operation.get("parameters", []) if p["in"] == "query"}
    body = operation.get("requestBody", {}).get("content", {}).get("application/json", {})
    schema = body.get("schema", {})
    if "$ref" in schema:
        # FastAPI publishes a body built from several fields as a named component.
        schema = contract["components"]["schemas"][schema["$ref"].rsplit("/", 1)[-1]]
    return names | set(schema.get("properties", {}))


def test_every_class_has_the_same_parameters_in_both_doors(exposure, cli, contract):
    for exposed in exposure.classes.values():
        expected = {p.name for p in exposed.parameters}
        assert _cli_parameters(cli.commands[exposed.scope]) == expected, exposed.scope
        assert _api_parameters(contract, exposed.path) == expected, exposed.path


def test_every_hand_path_has_the_same_parameters_in_both_doors(exposure, cli, contract):
    for path, methods in exposure.hand_paths.items():
        method = "get" if "get" in methods else next(iter(methods))
        scope = path.strip("/")
        assert _cli_parameters(cli.commands[scope]) == _api_parameters(contract, path, method), path


def test_no_door_has_a_scope_the_other_lacks(exposure, cli, contract):
    scopes = {exposed.scope for exposed in exposure.classes.values()}
    scopes |= {path.strip("/") for path in exposure.hand_paths}
    assert set(cli.commands) == scopes
    paths = {f"/{scope}" for scope in scopes}
    published = {p for p in contract["paths"] if not p.startswith("/openapi")}
    assert paths <= published
    # The API adds only the infrastructure routes beside the scopes.
    assert published - paths <= {"/", "/health", "/ready", "/version", "/classes"}


@pytest.mark.parametrize(
    "args",
    [
        ["taxonomy"],
        ["risk", "--isDefinedByTaxonomy", "nist-ai-rmf"],
        ["risk", "atlas-toxic-output", "--related_ids"],
        ["group", "--type", "CapabilityGroup"],
        ["obligation", "--hasEvidenceCategory", "TECHNICAL_IMPLEMENTATION"],
        ["adapter", "--hasAdapterType", "LORA"],
        ["control", "--hasRelatedRisk", "atlas-toxic-output", "--related"],
        ["model", "--performsTask", "code-generation"],
        ["stakeholder", "--isPartOf", "csiro-stakeholder-group-organization-level"],
    ],
)
def test_the_same_question_gets_the_same_count(cli, client, args):
    scope, *rest = args
    params: dict[str, str] = {}
    key = None
    for token in rest:
        if token.startswith("--"):
            key = token[2:]
            params[key] = "true"
        elif key is None:
            params["id"] = token
        else:
            params[key] = token
            key = None
    api_count = client.get(f"/{scope}", params=params).json()["count"]
    result = CliRunner().invoke(cli, [*args, "--count", "--mode", "local"])
    assert result.exit_code == 0, result.output
    assert int(result.output.strip()) == api_count


def test_a_record_reads_the_same_through_both_doors(cli, client):
    api_item = client.get("/taxonomy", params={"id": "nist-ai-rmf"}).json()["item"]
    result = CliRunner().invoke(cli, ["taxonomy", "nist-ai-rmf", "--mode", "local"])
    assert result.exit_code == 0, result.output
    assert '"id": "nist-ai-rmf"' in result.output
    assert api_item["id"] == "nist-ai-rmf"
