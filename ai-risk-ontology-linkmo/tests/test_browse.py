"""The browse database follows the schema, holds every record, and Datasette serves it.

Skipped until the browse dependency group is installed: linkml, sqlite-utils and datasette.
"""

from __future__ import annotations

import asyncio
import sqlite3

import pytest
import yaml

pytest.importorskip("linkml", reason="the browse dependency group is not installed")
pytest.importorskip("sqlite_utils", reason="the browse dependency group is not installed")
pytest.importorskip("datasette", reason="the browse dependency group is not installed")

from datasette.app import Datasette  # noqa: E402

from ai_risk_ontology_linkmo.browse import build, quote, search_tables, table_columns, text_columns  # noqa: E402
from ai_risk_ontology_linkmo.schema import schema_view  # noqa: E402
from ai_risk_ontology_linkmo.sources import rows_by_class  # noqa: E402


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    return build(tmp_path_factory.mktemp("browse"))


@pytest.fixture(scope="module")
def rows():
    return rows_by_class()


def count(connection: sqlite3.Connection, table: str) -> int:
    return connection.execute(f"select count(*) from {quote(table)}").fetchone()[0]


def test_each_class_table_holds_its_records_and_its_subclasses(built, rows):
    view = schema_view()
    with sqlite3.connect(built.path) as connection:
        tables = table_columns(connection)
        for class_name in tables:
            if class_name not in view.all_classes():
                continue
            key = view.get_identifier_slot(class_name)
            expected = sum(
                len(records)
                for other, records in rows.items()
                if class_name in view.class_ancestors(other)
                and key is not None
                and getattr(view.get_identifier_slot(other), "name", None) == key.name
            )
            assert count(connection, class_name) == expected, class_name


def test_search_finds_a_record_by_a_word_of_its_label(built, rows):
    view = schema_view()
    with sqlite3.connect(built.path) as connection:
        tables = table_columns(connection)
        for table in built.searchable:
            label, _ = text_columns(view, table, tables[table])
            if not label:
                continue
            value = connection.execute(f"select {quote(label)} from {quote(table)} where {quote(label)} is not null").fetchone()
            if value is None:
                continue
            word = str(value[0]).split()[0]
            found = connection.execute(
                f"select count(*) from {quote(table + '_fts')} where {quote(table + '_fts')} match ?", (f'"{word}"',)
            ).fetchone()[0]
            assert found >= 1, table
            return
    pytest.skip("no searchable table has a label")


def test_empty_tables_are_hidden_and_full_ones_described(built):
    metadata = yaml.safe_load(built.metadata.read_text(encoding="utf-8"))
    tables = metadata["databases"][built.path.stem]["tables"]
    with sqlite3.connect(built.path) as connection:
        hidden = search_tables(connection)
        counts = {t: count(connection, t) for t in table_columns(connection) if t not in hidden}
    full = [t for t, n in counts.items() if n]
    assert full and all("description" in tables[t] for t in full)
    assert not any(tables[t].get("hidden") for t in full)


def test_datasette_serves_the_folder_as_just_browse_does(built):
    table = next(t for t in built.searchable) if built.searchable else None
    if table is None:
        pytest.skip("no table has rows")

    async def get(path: str):
        return await Datasette(config_dir=built.path.parent).client.get(path)

    response = asyncio.run(get(f"/{built.path.stem}/{table}.json?_shape=array"))
    assert response.status_code == 200
    assert response.json()
