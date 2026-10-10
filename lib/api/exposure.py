"""Read the exposure file and the ontology schema into one view for the two kernels.

The CLI kernel (``lib/cli/cli.py``) and the API kernel (``lib/api/server_kernel.py``) both
ask the same questions: which classes are exposed, under which path, and which parameters
each one takes. The answers come from two places. ``lib/api/api.yaml`` names the classes,
their paths and the hand-written operations. The LinkML schema shipped inside the installed
``ai_atlas_nexus`` package gives each class its slots, and a slot becomes one parameter.
This module joins the two so that neither kernel reads YAML or ``SchemaView`` itself.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from linkml_runtime.utils.schemaview import SchemaView

API_FILE = Path(__file__).with_name("api.yaml")

# The parameters every class listing takes beside its slots. ``related`` and
# ``related_ids`` need a risk to relate to, so they come with ``hasRelatedRisk`` and only on
# classes the exposure file marks ``related``. The descriptions live in the overlay so that
# the published contract carries them too.
COMMON_PARAMETERS = ("byod",)
RELATED_PARAMETERS = ("hasRelatedRisk", "related", "related_ids")

# LinkML types that are not strings. Everything else, including references to other classes,
# enums and ``Any``, is passed as a string.
_KIND_BY_TYPE = {
    "integer": "integer",
    "float": "number",
    "double": "number",
    "decimal": "number",
    "boolean": "boolean",
}


@dataclass(frozen=True)
class Parameter:
    """One query parameter of a class listing, which is also one CLI option."""

    name: str
    kind: str  # "string", "boolean", "integer" or "number"
    description: str = ""
    # Permissible values when the slot's range is an enum with values. An enum without
    # values, such as ``Jurisdiction``, is a free string.
    choices: tuple[str, ...] = ()
    # A multivalued slot still takes one value: a record matches when its list holds it.
    multivalued: bool = False
    # True for a slot of the class, False for byod and the related parameters.
    slot: bool = True


@dataclass(frozen=True)
class ExposedClass:
    """A class the API lists and the CLI offers as a scope."""

    name: str
    path: str
    operation_id: str
    related: bool
    description: str
    parameters: tuple[Parameter, ...]

    @property
    def scope(self) -> str:
        """The CLI scope, which is the path without its slash: ``/risk`` is ``risk``."""
        return self.path.strip("/")

    @property
    def slot_names(self) -> tuple[str, ...]:
        return tuple(p.name for p in self.parameters if p.slot)

    def parameter(self, name: str) -> Parameter | None:
        return next((p for p in self.parameters if p.name == name), None)


@dataclass(frozen=True)
class Exposure:
    classes: dict[str, ExposedClass]
    overlay: dict[str, Any]
    schema_view: SchemaView = field(repr=False, compare=False)

    @property
    def by_scope(self) -> dict[str, ExposedClass]:
        return {c.scope: c for c in self.classes.values()}

    @property
    def by_path(self) -> dict[str, ExposedClass]:
        return {c.path: c for c in self.classes.values()}

    @property
    def hand_paths(self) -> dict[str, Any]:
        """The operations written by hand: graph, crosswalk, inference, schemaview, byo, ares."""
        return self.overlay.get("paths", {})

    def common_parameter(self, name: str) -> dict[str, Any]:
        """The OpenAPI definition of byod, related, related_ids or hasRelatedRisk."""
        return self.overlay["components"]["parameters"][name]


def schema_directory() -> Path:
    """The LinkML schema the installed ``ai_atlas_nexus`` package ships."""
    import ai_atlas_nexus

    return Path(ai_atlas_nexus.__file__).parent / "ai_risk_ontology" / "schema"


@lru_cache(maxsize=None)
def schema_view() -> SchemaView:
    """One ``SchemaView`` over the ontology with its imports merged."""
    schema_dir = schema_directory()
    modules = [f[:-5] for f in os.listdir(schema_dir) if f.endswith(".yaml")]
    # LinkML appends .yaml to importmap targets itself, so the map points at the stem.
    importmap = {stem: str(schema_dir / stem) for stem in modules}
    return SchemaView(
        str(schema_dir / "ai-risk-ontology.yaml"), merge_imports=True, importmap=importmap
    )


def _parameter_from_slot(view: SchemaView, slot) -> Parameter:
    choices: tuple[str, ...] = ()
    enums = view.all_enums()
    kind = "string"
    if slot.range in enums:
        choices = tuple(enums[slot.range].permissible_values.keys())
    elif slot.range in view.all_types():
        # The root of the type's ``typeof`` chain says whether it is a number or a boolean.
        root = view.type_ancestors(slot.range)[-1]
        kind = _KIND_BY_TYPE.get(root, "string")
    return Parameter(
        name=slot.name,
        kind=kind,
        description=(slot.description or "").strip(),
        choices=choices,
        multivalued=bool(slot.multivalued),
    )


def _common_parameter(overlay: dict[str, Any], name: str) -> Parameter:
    definition = overlay["components"]["parameters"][name]
    return Parameter(
        name=name,
        kind=definition.get("schema", {}).get("type", "string"),
        description=definition.get("description", ""),
        slot=False,
    )


@lru_cache(maxsize=None)
def load_exposure(api_file: Path = API_FILE) -> Exposure:
    """Read the exposure file once and resolve every exposed class against the schema."""
    with open(api_file, encoding="utf-8") as handle:
        config = yaml.safe_load(handle)["generator_args"]["openapi"]
    overlay = config.get("overlay", {})
    view = schema_view()
    classes: dict[str, ExposedClass] = {}
    for name, entry in config["expose"]["classes"].items():
        definition = view.get_class(name)
        if definition is None:
            raise ValueError(f"{api_file.name} exposes {name}, which the schema does not define")
        related = bool(entry.get("related", False))
        parameters = [_common_parameter(overlay, n) for n in COMMON_PARAMETERS]
        parameters += [_parameter_from_slot(view, s) for s in view.class_induced_slots(name)]
        if related:
            slot_names = {p.name for p in parameters}
            parameters += [
                _common_parameter(overlay, n) for n in RELATED_PARAMETERS if n not in slot_names
            ]
        classes[name] = ExposedClass(
            name=name,
            path=entry["path"],
            operation_id=entry.get("operation_id", f"list_{name.lower()}"),
            related=related,
            description=(definition.description or "").strip(),
            parameters=tuple(parameters),
        )
    return Exposure(classes=classes, overlay=overlay, schema_view=view)
