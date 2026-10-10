"""Load the AI Risk Ontology data into a DuckDB store through linkml-store.

The ai-atlas-nexus library re-parses every YAML file each time it starts, which is why a
local-mode CLI call takes several seconds. This module loads the same data once into a
DuckDB file that linkml-store queries in milliseconds, and the API and the CLI read it when
``AI_LINKMO_DATA_SOURCE`` says so (see ``lib/store/source.py``).

Two choices were measured before they were made (see the research behind the roadmap).
The library's own loader, ``load_yamls_to_container``, is reused so that the mapping rows
split across files are merged into their records by id exactly as the library does it, and
so that the bring-your-own-data files are read the same way. The rows are then grouped by
their concrete class and stored one collection per class, because a linkml-store DuckDB
collection keeps only the columns of its declared class: a ``Risk`` stored in the
polymorphic ``entries`` collection would silently lose ``risk_type`` and ``hasRelatedAction``.

The store is a build artefact. ``just load-store`` writes two databases under
``lib/store/data/``, one for the packaged data and one with the ``byo/data`` files added,
and a linkml-store config beside them so that its command line, ``linkml-store -C
lib/store/data/config.yaml``, can validate and search them.
"""

from __future__ import annotations

import importlib.metadata
import logging
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import yaml

logger = logging.getLogger(__name__)


def widen_duckdb_types() -> None:
    """Store LinkML integers, floats and booleans in DuckDB without loss.

    linkml-store 0.3.2 maps ``integer`` to a 32-bit column and ``float`` to a 4-byte one, and
    leaves ``boolean`` and ``double`` as text, so ``numParameters: 3000000000`` fails to insert
    (linkml/linkml-store#85, fixed by the open PR #86). Until that merges, the mapping table
    the DuckDB backend reads is widened here, which affects only tables created afterwards.
    """
    import sqlalchemy

    from linkml_store.api.stores.duckdb.mappings import TMAP

    TMAP.update(
        {
            "integer": sqlalchemy.BigInteger,
            "float": sqlalchemy.Double,
            "double": sqlalchemy.Double,
            "decimal": sqlalchemy.Double,
            "boolean": sqlalchemy.Boolean,
        }
    )

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "lib" / "store" / "data"
CONFIG_FILE = DATA_DIR / "config.yaml"
BYO_DATA_DIR = PROJECT_ROOT / "byo" / "data"

# The two databases mirror the two AIAtlasNexus instances the server keeps.
DATABASES = {False: "atlas", True: "byod"}


def database_path(byod: bool, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"{DATABASES[byod]}.duckdb"


@lru_cache(maxsize=1)
def _reserved_words() -> frozenset[str]:
    import duckdb

    rows = duckdb.sql(
        "select keyword_name from duckdb_keywords() where keyword_category = 'reserved'"
    ).fetchall()
    return frozenset(name.upper() for (name,) in rows)


def collection_name(class_name: str) -> str:
    """The store collection that holds a class, which is its name unless SQL reserves it.

    linkml-store writes the collection name into SQL unquoted, so ``Group`` cannot be a
    table; it is stored as ``GroupRecords`` instead. The config still says ``type: Group``.
    """
    return f"{class_name}Records" if class_name.upper() in _reserved_words() else class_name


def rows_by_class(container: Any) -> dict[str, list[dict[str, Any]]]:
    """Group every record of the container by its concrete class, as plain dicts.

    ``model_dump(mode="json")`` turns enum members into their values and dates into strings,
    which is what the store can hold and what the API returns anyway. Fields that are None are
    left out so that the store's columns stay sparse rather than full of nulls.
    """
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for slot in type(container).model_fields:
        for record in getattr(container, slot) or []:
            rows[type(record).__name__].append(record.model_dump(mode="json", exclude_none=True))
    return dict(rows)


def load_container(byod: bool):
    """The library's merged view of the data, with the byo files when ``byod`` is set."""
    from ai_atlas_nexus.toolkit.data_utils import load_yamls_to_container

    return load_yamls_to_container(str(BYO_DATA_DIR) if byod else None)


def build_database(byod: bool, data_dir: Path = DATA_DIR) -> dict[str, int]:
    """Write one DuckDB file for ``byod`` and return the row count per collection.

    The file is rebuilt from nothing each time. A rebuild only inserts, which is the one
    write path linkml-store's DuckDB backend gets right under every SQLAlchemy it accepts
    (linkml/linkml-store#93 covers the others), and it is also simpler than reconciling.
    """
    from linkml_store import Client

    from lib.api.exposure import schema_view

    widen_duckdb_types()
    data_dir.mkdir(parents=True, exist_ok=True)
    path = database_path(byod, data_dir)
    if path.exists():
        path.unlink()
    rows = rows_by_class(load_container(byod))
    client = Client()
    database = client.attach_database(f"duckdb:///{path}", alias=DATABASES[byod])
    database.set_schema_view(schema_view())
    counts: dict[str, int] = {}
    for class_name in sorted(rows):
        collection = database.create_collection(class_name, alias=collection_name(class_name))
        collection.insert(rows[class_name])
        counts[class_name] = len(rows[class_name])
    database.commit()
    logger.info("Loaded %d collections into %s", len(counts), path)
    return counts


def open_database(byod: bool, data_dir: Path = DATA_DIR):
    """Attach a built database for reading, with the schema view it needs.

    A database reattached from its file knows nothing about the schema, so without this
    step ``get_one`` has no identifier to look up (linkml/linkml-store#102). Raises
    ``FileNotFoundError`` with the recipe to run when the store has not been built.
    """
    from linkml_store import Client

    from lib.api.exposure import schema_view

    path = database_path(byod, data_dir)
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist; run `just load-store` to build the store")
    database = Client().attach_database(f"duckdb:///{path}", alias=DATABASES[byod])
    database.set_schema_view(schema_view())
    return database


def write_config(counts_by_database: dict[str, dict[str, int]], data_dir: Path = DATA_DIR) -> Path:
    """Write the linkml-store client config that describes the databases just built.

    Every collection is declared with its class as ``type``, which is what makes
    ``linkml-store validate`` check each row against the right class. The schema location is
    the installed package's, so the file is generated with the store rather than committed.
    """
    from lib.api.exposure import schema_directory

    schema = schema_directory() / "ai-risk-ontology.yaml"
    config = {
        "generated_by": "just load-store",
        "ai_atlas_nexus": importlib.metadata.version("ai-atlas-nexus"),
        "databases": {
            alias: {
                "handle": f"duckdb:///{data_dir / alias}.duckdb",
                "schema_location": str(schema),
                "collections": {collection_name(name): {"type": name} for name in sorted(counts)},
            }
            for alias, counts in counts_by_database.items()
        },
    }
    path = data_dir / "config.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path


def build_all(data_dir: Path = DATA_DIR, which: Iterable[bool] = (False, True)) -> Path:
    """Build the requested databases and the config that describes them."""
    counts = {DATABASES[byod]: build_database(byod, data_dir) for byod in which}
    return write_config(counts, data_dir)
