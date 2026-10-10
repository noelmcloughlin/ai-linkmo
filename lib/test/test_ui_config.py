"""The UI's entity list is the exposure file's class list, and its filter overlay is valid.

``lib/frontend/src/lib/entities.json`` is written by ``just gen-ui-config``. The first tests
check that the generator follows the exposure and that the committed file is current. The
last ones read the hand-written overlay in ``constants.ts`` and check every filter name
against the schema, because the API answers 422 to a filter that is not a parameter of the
class.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from lib.api.exposure import load_exposure
from scripts.gen_ui_config import build_config, main, render

ROOT = Path(__file__).resolve().parents[2]
ENTITIES = ROOT / "lib" / "frontend" / "src" / "lib" / "entities.json"
CONSTANTS = ROOT / "lib" / "frontend" / "src" / "lib" / "constants.ts"


@pytest.fixture(scope="module")
def exposure():
    return load_exposure()


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    output = tmp_path_factory.mktemp("ui") / "entities.json"
    assert main([str(output)]) == 0
    return json.loads(output.read_text(encoding="utf-8"))


def test_endpoint_keys_are_the_exposure_scopes(exposure, generated):
    assert [e["key"] for e in generated["endpoints"]] == list(exposure.by_scope)
    assert [e["path"] for e in generated["endpoints"]] == list(exposure.by_path)
    assert generated["generated_by"] == "just gen-ui-config"


def test_the_committed_entities_file_is_current():
    assert ENTITIES.is_file(), "run `just gen-ui-config` to write entities.json"
    assert ENTITIES.read_text(encoding="utf-8") == render(build_config()), (
        "entities.json is behind the exposure file or the schema; run `just gen-ui-config`"
    )


def test_derived_filters_and_byo_sections_are_valid(exposure, generated):
    view = exposure.schema_view
    container_slots = {s.name for s in view.class_induced_slots("Container")}
    for entry in generated["endpoints"]:
        exposed = exposure.by_scope[entry["key"]]
        assert entry["type"] == exposed.name
        assert set(entry["filters"]) <= set(exposed.slot_names), entry["key"]
        assert entry["prominent"][:3] == ["id", "name", "description"]
        assert entry["byo"] in container_slots, entry["key"]


def overlay_filters() -> dict[str, list[str]]:
    """Parse ``UI_FILTER_OVERLAY`` out of constants.ts without a TypeScript parser.

    The object holds only string arrays keyed by endpoint, so a regex over the block between
    its opening brace and the closing ``};`` is enough.
    """
    source = CONSTANTS.read_text(encoding="utf-8")
    match = re.search(r"const UI_FILTER_OVERLAY[^{]*\{(.*?)\n\};", source, re.S)
    assert match, "UI_FILTER_OVERLAY not found in constants.ts"
    body = re.sub(r"//[^\n]*", "", match.group(1))
    return {
        key: re.findall(r'"([^"]+)"', names)
        for key, names in re.findall(r"(\w+):\s*\[(.*?)\]", body, re.S)
    }


def test_overlay_filters_are_parameters_of_their_class(exposure):
    overlay = overlay_filters()
    assert overlay, "the overlay parsed as empty"
    for key, names in overlay.items():
        exposed = exposure.by_scope.get(key)
        assert exposed is not None, f"overlay names {key}, which api.yaml does not expose"
        parameters = {p.name for p in exposed.parameters}
        unknown = [n for n in names if n not in parameters]
        assert not unknown, f"{key}: {unknown} are not parameters of {exposed.name}"
