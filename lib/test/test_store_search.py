"""Search ranks records by their text through the persisted index, and the dump reads back.

The store is built in a temporary directory, so ``lib/store/data`` is never touched, and
only the ``risk`` scope is indexed, which is what lets the 409 be tested.
"""

from __future__ import annotations

import json

import pytest
import yaml
from fastapi import HTTPException

from lib.api.exposure import schema_view
from lib.store.loader import build_database
from lib.store.search import index_database, search
from scripts.dump_store import dump_database


@pytest.fixture(scope="module")
def data_dir(tmp_path_factory):
    directory = tmp_path_factory.mktemp("store")
    build_database(byod=False, data_dir=directory)
    classes_before = len(schema_view().all_classes())
    report = index_database(False, data_dir=directory, scopes=["risk"])
    assert (report[0].class_name, report[0].rows) == ("Risk", 630)
    assert report[0].seconds > 0
    # Indexing induces classes for the shadow tables into the shared schema view; they
    # must not stay there, or every count of the schema in this process would drift.
    assert len(schema_view().all_classes()) == classes_before
    return directory


def test_search_ranks_the_named_risk_first(data_dir):
    result = search("toxic output", scope="risk", data_dir=data_dir)
    assert result["query"] == "toxic output"
    assert result["count"] == len(result["items"]) == 20
    first = result["items"][0]
    assert first["id"] == "atlas-toxic-output"
    assert first["type"] == "Risk"
    assert isinstance(first["score"], float) and first["score"] > 0.5
    scores = [item["score"] for item in result["items"]]
    assert scores == sorted(scores, reverse=True)
    # The record is the stored one, without its null columns, and it serialises as JSON.
    assert first["name"] == "Toxic output" and None not in first.values()
    json.dumps(result)


def test_limit_is_honoured(data_dir):
    result = search("toxic output", scope="risk", limit=3, data_dir=data_dir)
    assert result["count"] == len(result["items"]) == 3
    assert result["items"][0]["id"] == "atlas-toxic-output"


def test_unknown_scope_is_422(data_dir):
    with pytest.raises(HTTPException) as raised:
        search("toxic output", scope="nosuch", data_dir=data_dir)
    assert raised.value.status_code == 422
    assert "nosuch is not a scope" in raised.value.detail


def test_a_query_without_a_trigram_is_422(data_dir):
    with pytest.raises(HTTPException) as raised:
        search("ab", scope="risk", data_dir=data_dir)
    assert raised.value.status_code == 422


def test_a_scope_without_an_index_is_409(data_dir):
    with pytest.raises(HTTPException) as raised:
        search("toxic output", scope="control", data_dir=data_dir)
    assert raised.value.status_code == 409
    assert "just index-store" in raised.value.detail and "Action" in raised.value.detail


def test_a_missing_store_is_503(data_dir):
    # Only the atlas database was built here.
    with pytest.raises(HTTPException) as raised:
        search("toxic output", byod=True, data_dir=data_dir)
    assert raised.value.status_code == 503
    assert "just load-store" in raised.value.detail


def test_dump_writes_one_file_per_database_keyed_by_class(data_dir, tmp_path):
    path = dump_database(False, tmp_path, data_dir=data_dir)
    assert path == tmp_path / "atlas.yaml"
    dump = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "Risk" in dump and "Group" in dump
    assert len(dump["Risk"]) == 630
    assert not any(key.startswith("internal__") or key == "GroupRecords" for key in dump)
    assert all(None not in row.values() for row in dump["Group"])
    as_json = dump_database(False, tmp_path, data_dir=data_dir, fmt="json")
    assert set(json.loads(as_json.read_text(encoding="utf-8"))) == set(dump)
