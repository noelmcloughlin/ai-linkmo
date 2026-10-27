"""The published contract and entity list are current, and the references are served.

`just gen-openapi` writes the contract where the openapi_file answer says, and
`just gen-ui-config` the entity list where the entities_file answer says. Each test of a
file is skipped until the project publishes it.
"""

from __future__ import annotations

import json

import pytest
from linkmo_cases import load_script

from ai_linkmo.settings import entities_path, openapi_path

CONTRACT = openapi_path()
ENTITIES = entities_path()


@pytest.mark.skipif(not CONTRACT.is_file(), reason="run `just gen-openapi` to publish the contract")
def test_the_published_contract_is_current(contract):
    export = load_script("export_openapi")
    assert CONTRACT.read_text(encoding="utf-8") == export.render(export.build_contract()), (
        f"{CONTRACT} is behind the exposure file or the schema; run `just gen-openapi`"
    )
    assert json.loads(CONTRACT.read_text(encoding="utf-8")) == contract


@pytest.mark.skipif(not ENTITIES.is_file(), reason="run `just gen-ui-config` to write the entity list")
def test_the_entity_list_is_current():
    ui = load_script("gen_ui_config")
    assert ENTITIES.read_text(encoding="utf-8") == ui.render(ui.build_config()), (
        f"{ENTITIES} is behind the exposure file or the schema; run `just gen-ui-config`"
    )


def test_the_contract_is_openapi_3_1_with_a_model_per_class(exposure, contract):
    assert contract["openapi"].startswith("3.1")
    schemas = contract["components"]["schemas"]
    for exposed in exposure.classes.values():
        assert f"Envelope_{exposed.name}" in schemas, exposed.name
        assert exposed.name in schemas, exposed.name


def test_the_entity_list_follows_the_exposure(exposure):
    config = load_script("gen_ui_config").build_config(exposure)
    assert [e["key"] for e in config["endpoints"]] == list(exposure.by_scope)
    for entry in config["endpoints"]:
        assert set(entry["filters"]) <= set(exposure.by_scope[entry["key"]].slot_names)


def test_the_references_are_served(client):
    for path in ("/docs", "/redoc", "/scalar"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "text/html" in response.headers["content-type"], path
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").status_code == 200
