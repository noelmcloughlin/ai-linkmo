"""The command line and the API are one interface and give one answer.

Both kernels read one exposure, so what has to hold is that neither differs from it or
from the other: every command is an endpoint with the same parameters, and the same
question gets the same JSON through the command line in local mode and through the API.
"""

from __future__ import annotations

import json

import click
import pytest
from linkmo_cases import case_id, load_cases, to_query

from ai_risk_ontology_linkmo.cli import SHARED_OPTION_NAMES

CASES = load_cases()


def _cli_parameters(command: click.Command) -> set[str]:
    """The names a command takes from the user, without the shared options."""
    return {p.name for p in command.params} - set(SHARED_OPTION_NAMES)


def _api_parameters(contract, path: str, method: str = "get") -> set[str]:
    operation = contract["paths"][path][method]
    names = {p["name"] for p in operation.get("parameters", []) if p["in"] == "query"}
    body = operation.get("requestBody", {}).get("content", {}).get("application/json", {})
    schema = body.get("schema", {})
    if "$ref" in schema:
        schema = contract["components"]["schemas"][schema["$ref"].rsplit("/", 1)[-1]]
    return names | set(schema.get("properties", {}))


def test_every_class_has_the_same_parameters_in_both_doors(exposure, cli, contract):
    for exposed in exposure.classes.values():
        assert _cli_parameters(cli.commands[exposed.scope]) == {p.python_name for p in exposed.parameters}
        assert _api_parameters(contract, exposed.path) == {p.name for p in exposed.parameters}


def test_every_hand_operation_has_the_same_parameters_in_both_doors(exposure, cli, contract):
    for path, methods in exposure.hand_paths.items():
        method = "get" if "get" in methods else next(iter(methods))
        command = cli.commands[path.strip("/")]
        assert _cli_parameters(command) == _api_parameters(contract, path, method), path


def test_no_door_has_a_command_the_other_lacks(exposure, cli, contract):
    scopes = {exposed.scope for exposed in exposure.classes.values()}
    scopes |= {path.strip("/") for path in exposure.hand_paths}
    assert set(cli.commands) == scopes
    assert set(contract["paths"]) == {f"/{scope}" for scope in scopes}


@pytest.mark.parametrize("case", CASES, ids=case_id)
def test_the_same_question_gets_the_same_answer(exposure, cli, client, runner, case):
    path, params = to_query(exposure, case["args"])
    api = client.get(path, params=params)
    assert api.status_code == 200, api.text
    result = runner.invoke(cli, [*map(str, case["args"]), "--mode", "local"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == api.json()


def test_a_bad_enum_value_is_refused_by_both_doors(exposure, cli, client, runner):
    for exposed in exposure.classes.values():
        choice = next((p for p in exposed.parameters if p.choices), None)
        if choice is None:
            continue
        assert client.get(exposed.path, params={choice.name: "no-such-value"}).status_code == 422
        result = runner.invoke(cli, [exposed.scope, f"--{choice.name}", "no-such-value", "--mode", "local"])
        assert result.exit_code == 2
        return
    pytest.skip("no exposed class has an enum slot with values")
