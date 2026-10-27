"""Where the project finds its schema, its datamodel, its exposure file and its data.

The values come from the answers the linkmo copier template recorded in
``.copier-answers.linkmo.yml`` at the host root, and ``copier update`` rewrites this
file when an answer changes. Each value can be replaced for one run by the environment
variable named beside it, which is how a test points the project at a fixture.

A path is read from the host root unless it is absolute. A schema or a data directory
that is inside an installed package is written ``pkg:<package>/<path>``.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parents[1]
HOST_ROOT = PROJECT_DIR.parent

ENV_PREFIX = "AI_LINKMO"
COMMAND_NAME = "ai"
DISTRIBUTION = "ai-risk-ontology-linkmo"


def _setting(name: str, default: str) -> str:
    return os.environ.get(f"{ENV_PREFIX}_{name}", default)


# AI_LINKMO_SCHEMA: the LinkML schema.
SCHEMA = _setting("SCHEMA", "pkg:ai_atlas_nexus/ai_risk_ontology/schema/ai-risk-ontology.yaml")
# AI_LINKMO_DATAMODEL: the module gen-pydantic wrote from the schema.
DATAMODEL_MODULE = _setting("DATAMODEL", "ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology")
# AI_LINKMO_ROOT_CLASS: the class a data file holds; empty means the tree_root class.
ROOT_CLASS = _setting("ROOT_CLASS", "")
# AI_LINKMO_EXPOSURE: the exposure file, read from the project folder unless absolute.
EXPOSURE = _setting("EXPOSURE", "exposure.yaml")
# AI_LINKMO_DATA_SOURCE: "yaml" for a directory of instance files, "python" for an object.
DATA_SOURCE = _setting("DATA_SOURCE", "yaml")
# AI_LINKMO_DATA: the directory of instance files, or the object as module:attribute.
DATA = _setting("DATA", "pkg:ai_atlas_nexus/data/knowledge_graph")

# Folders put on sys.path before the datamodel is imported, when they exist. The sidecar's
# src/ is one, because gen-pydantic writes the datamodel there.
MODULE_PATHS = [HOST_ROOT / ".linkml" / "src"]


def host_path(value: str, base: Path = HOST_ROOT) -> Path:
    """Resolve a path setting: ``pkg:`` inside an installed package, else from ``base``.

    The package is found without being imported, so a heavy package costs nothing here.
    """
    if value.startswith("pkg:"):
        package, _, inner = value[len("pkg:") :].partition("/")
        spec = importlib.util.find_spec(package)
        if spec is None or not spec.submodule_search_locations:
            raise FileNotFoundError(
                f"{value}: no installed package named {package}. Add its distribution to the "
                "requirements answer, or set LINKMO_PYTHON to a Python that has it."
            )
        return Path(list(spec.submodule_search_locations)[0]) / inner
    path = Path(value).expanduser()
    return path if path.is_absolute() else base / path


def schema_path() -> Path:
    return host_path(SCHEMA)


def exposure_path() -> Path:
    return host_path(EXPOSURE, PROJECT_DIR)


def data_path() -> Path:
    return host_path(DATA)
