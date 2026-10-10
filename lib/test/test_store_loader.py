"""The DuckDB store holds the same records the library holds, one collection per class."""

from __future__ import annotations

import yaml
import pytest

from lib.store.loader import build_all, database_path, rows_by_class


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp("store")
    config = build_all(data_dir, which=(False,))
    return data_dir, yaml.safe_load(config.read_text())


def test_rows_are_grouped_by_concrete_class():
    from lib.store.loader import load_container

    rows = rows_by_class(load_container(byod=False))
    # Risks live in the polymorphic ``entries`` slot but are stored as their own class.
    assert "Risk" in rows and "Entry" not in rows
    assert all("id" in row for row in rows["Risk"])
    # Enum members come out as their values.
    assert any(row.get("hasAdapterType") == ["LORA"] for row in rows["Adapter"])


def test_config_declares_every_collection_with_its_type(store):
    data_dir, config = store
    database = config["databases"]["atlas"]
    assert database["handle"].endswith(str(database_path(False, data_dir)))
    assert database["collections"]["Risk"] == {"type": "Risk"}
    assert "byod" not in config["databases"]


def test_subclass_slots_survive_and_filters_work(store):
    from lib.store.loader import open_database

    data_dir, config = store
    database = open_database(byod=False, data_dir=data_dir)
    risks = database.get_collection("Risk")
    nist = risks.find({"isDefinedByTaxonomy": "nist-ai-rmf"})
    assert nist.num_rows == 12
    toxic = risks.get_one("atlas-toxic-output")
    assert toxic["name"] == "Toxic output"
    # A Risk-only slot would have been dropped in a collection typed as ``Entry``.
    assert any("hasRelatedAction" in row for row in risks.find({}, limit=1000).rows)
    # A list slot is filtered with ``$contains``.
    adapters = database.get_collection("Adapter")
    assert adapters.find({"hasAdapterType": {"$contains": "LORA"}}).num_rows == 19
