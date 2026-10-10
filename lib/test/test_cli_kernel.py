"""The CLI command tree matches the exposure.

These tests build the click group from ``load_exposure()`` and check the invariants the
kernel promises: one command per exposed class with one option per parameter, the names kept
in camelCase, enum slots offered as choices, and one command per hand path. None of them
needs the server or loads the ontology data; the schema alone is read.
"""

from __future__ import annotations

import sys

import click
import pytest
from click.testing import CliRunner

from lib.api.exposure import load_exposure
from lib.cli.cli import SHARED_OPTION_NAMES, build_cli


@pytest.fixture(scope="module")
def exposure():
    return load_exposure()


@pytest.fixture(scope="module")
def cli(exposure):
    return build_cli(exposure)


def _option_names(command: click.Command) -> set[str]:
    return {p.name for p in command.params if isinstance(p, click.Option)}


def _option(command: click.Command, name: str) -> click.Option:
    return next(p for p in command.params if isinstance(p, click.Option) and p.name == name)


def test_every_exposed_class_is_a_command_with_one_option_per_parameter(exposure, cli):
    for exposed in exposure.classes.values():
        command = cli.commands[exposed.scope]
        expected = {p.name for p in exposed.parameters if p.name != "id"}
        assert _option_names(command) == expected | set(SHARED_OPTION_NAMES), exposed.scope
        # The id is a positional argument, not an option.
        arguments = [p.name for p in command.params if isinstance(p, click.Argument)]
        assert arguments == ["id"], exposed.scope


def test_option_names_keep_their_case(cli):
    option = _option(cli.commands["risk"], "isDefinedByTaxonomy")
    assert option.opts == ["--isDefinedByTaxonomy"]
    assert _option(cli.commands["risk"], "related_ids").opts == ["--related_ids"]


def test_enum_slot_is_a_choice(cli):
    option = _option(cli.commands["adapter"], "hasAdapterType")
    assert isinstance(option.type, click.Choice)
    assert "LORA" in option.type.choices
    # A multivalued slot still takes one value.
    assert not option.multiple


def test_enum_without_values_is_a_free_string(cli):
    option = _option(cli.commands["risk"], "hasJurisdiction")
    assert option.type is click.STRING


def test_kinds_map_to_click_types(cli):
    model = cli.commands["model"]
    assert _option(model, "numParameters").type is click.INT
    assert _option(model, "byod").is_flag


def test_every_hand_path_is_a_command(exposure, cli):
    for path, methods in exposure.hand_paths.items():
        command = cli.commands[path.strip("/")]
        operation = methods.get("get") or next(iter(methods.values()))
        expected = {
            p["name"] for p in operation.get("parameters", []) if p.get("in") == "query"
        } - {"id"}
        body = operation.get("requestBody", {}).get("content", {}).get("application/json", {})
        expected |= set(body.get("schema", {}).get("properties", {}))
        assert _option_names(command) == expected | set(SHARED_OPTION_NAMES), path


def test_hand_path_id_is_positional(cli):
    arguments = [p.name for p in cli.commands["graph"].params if isinstance(p, click.Argument)]
    assert arguments == ["id"]


def test_bad_enum_value_exits_2_without_loading_the_ontology(cli):
    # Another test in the same process may have loaded the library already, so the check
    # is that this invocation did not load it, not that it was never loaded.
    loaded_before = "ai_atlas_nexus.library" in sys.modules
    result = CliRunner().invoke(cli, ["adapter", "--hasAdapterType", "NOPE", "--mode", "local"])
    assert result.exit_code == 2
    assert "Invalid value for '--hasAdapterType'" in result.output
    assert loaded_before or "ai_atlas_nexus.library" not in sys.modules


def test_unknown_scope_exits_2(cli):
    result = CliRunner().invoke(cli, ["invalid_scope_name", "--count"])
    assert result.exit_code == 2
    assert "error" in result.output.lower()


def test_group_help_names_the_demo_and_the_scope(cli):
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "AI-LinkMO CLI Demo" in result.output
    assert "scope" in result.output
    # The short -h works after the scope too, as docs/cli-examples.md says.
    assert CliRunner().invoke(cli, ["risk", "-h"]).exit_code == 0


def test_shared_options_resolve_from_either_level(cli, monkeypatch):
    """A flag before the scope and a flag after it both count; the command's mode wins."""
    import lib.cli.cli as cli_module

    seen = {}

    def fake_local(target, request, settings):
        seen["target"], seen["request"], seen["settings"] = target, request, settings

    monkeypatch.setattr(cli_module, "call_local_handler", fake_local)
    args = ["--mode", "api", "--count", "risk", "atlas-toxic-output", "--related", "--mode", "local"]
    result = CliRunner().invoke(cli, args)
    assert result.exit_code == 0, result.output
    assert seen["settings"].mode == "local" and seen["settings"].count
    assert seen["target"].class_name == "Risk" and seen["target"].path == "/risk"
    # Only what the user gave is passed on: no None and no False flag.
    assert seen["request"] == {"id": "atlas-toxic-output", "related": True}
