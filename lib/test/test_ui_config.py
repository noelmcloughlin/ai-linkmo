"""The UI's entity list is current, and its filter overlay is valid.

``lib/frontend/src/lib/entities.json`` is written by ``just gen-ui-config``, which runs the
linkmo project's script. That project's own tests check that the script follows the
exposure file. These check the committed file, each endpoint's Container slot, and the
hand-written overlay in ``constants.ts``, because the API answers 422 to a filter that is
not a parameter of the class.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

from lib.api.exposure import load_exposure as load_served_exposure
from ai_linkmo.exposure import load_exposure

ROOT = Path(__file__).resolve().parents[2]
ENTITIES = ROOT / "lib" / "frontend" / "src" / "lib" / "entities.json"
CONSTANTS = ROOT / "lib" / "frontend" / "src" / "lib" / "constants.ts"
SCRIPT = ROOT / "ai-risk-ontology-linkmo" / "scripts" / "gen_ui_config.py"


@pytest.fixture(scope="module")
def exposure():
    return load_exposure()


@pytest.fixture(scope="module")
def ui():
    spec = importlib.util.spec_from_file_location("linkmo_gen_ui_config", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_committed_entities_file_is_current(ui):
    assert ENTITIES.is_file(), "run `just gen-ui-config` to write entities.json"
    assert ENTITIES.read_text(encoding="utf-8") == ui.render(ui.build_config()), (
        "entities.json is behind the exposure file or the schema; run `just gen-ui-config`"
    )


def test_each_collection_is_a_container_slot(exposure, ui):
    container_slots = {s.name for s in exposure.schema_view.class_induced_slots("Container")}
    for entry in ui.build_config(exposure)["endpoints"]:
        assert entry["type"] == exposure.by_scope[entry["key"]].name
        assert entry["prominent"][:3] == ["id", "name", "description"]
        assert entry["collection"] in container_slots, entry["key"]


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


def test_overlay_filters_are_parameters_of_their_class():
    # The API is still the one lib/api/api.yaml describes, with the related parameters.
    exposure = load_served_exposure()
    overlay = overlay_filters()
    assert overlay, "the overlay parsed as empty"
    for key, names in overlay.items():
        exposed = exposure.by_scope.get(key)
        assert exposed is not None, f"overlay names {key}, which the exposure file does not expose"
        parameters = {p.name for p in exposed.parameters}
        unknown = [n for n in names if n not in parameters]
        assert not unknown, f"{key}: {unknown} are not parameters of {exposed.name}"
