"""The browse databases follow the schema, hold every record, and Datasette serves them.

The fast tests build a database from a toy schema written here, which has what the loader
must handle: an abstract parent that a reference points at, a tree root, a ``linkml:Any``
range, multivalued slots on a parent and on a child, an enum, and a class without records.
They also show the browse code names nothing of the ontology. The slow tests build both
databases of the real data, about twenty seconds, and check them against the library.
"""

from __future__ import annotations

import asyncio
import sqlite3

import pytest
import yaml
from linkml_runtime.utils.schemaview import SchemaView

pytest.importorskip("sqlite_utils", reason="the browse extra is not installed")
pytest.importorskip("datasette", reason="the browse extra is not installed")

from datasette.app import Datasette  # noqa: E402

from lib.browse.loader import (  # noqa: E402
    create_database,
    dangling_references,
    drop_empty_link_tables,
    enable_search,
    generate_ddl,
    load_rows,
    save,
    table_columns,
    table_schema,
)
from lib.browse.metadata import database_metadata  # noqa: E402

TOY_SCHEMA = """
id: https://example.org/toy
name: toy
prefixes:
  linkml: https://w3id.org/linkml/
  schema: http://schema.org/
  toy: https://example.org/toy/
default_prefix: toy
default_range: string
imports:
  - linkml:types
classes:
  Box:
    tree_root: true
    attributes:
      things:
        range: Thing
        multivalued: true
        inlined_as_list: true
  Any:
    class_uri: linkml:Any
  Thing:
    abstract: true
    description: Anything in the box.
    slots: [id, name, description, aliases, seeAlso]
  Group:
    is_a: Thing
    abstract: true
  Kit:
    is_a: Group
    description: A kit of parts.
  Part:
    is_a: Thing
    description: One part.
    slots: [partOf, size, related]
  Gadget:
    is_a: Thing
    description: A class with no records.
slots:
  id:
    identifier: true
    slot_uri: schema:identifier
  name:
    slot_uri: schema:name
    description: The name.
  description:
    slot_uri: schema:description
  aliases:
    multivalued: true
  seeAlso:
    range: Any
  partOf:
    range: Group
    description: The group the part belongs to.
  size:
    range: Size
  related:
    range: Part
    multivalued: true
enums:
  Size:
    permissible_values:
      small:
      large:
"""

TOY_ROWS = {
    "Kit": [{"id": "k1", "name": "Starter kit"}],
    "Part": [
        {
            "id": "p1",
            "name": "Copper widget",
            "description": "A widget made of copper.",
            "partOf": "k1",
            "size": "small",
            "related": ["p2"],
            "aliases": ["cw", "widget"],
            "seeAlso": "ext:1",
        },
        {"id": "p2", "name": "Brass sprocket", "partOf": "k1", "size": "large", "aliases": ["bs"]},
        {"id": "p3", "name": "Loose screw", "partOf": "no-such-kit", "size": "small"},
    ],
}


def count(connection: sqlite3.Connection, table: str) -> int:
    return connection.execute(f'select count(*) from "{table}"').fetchone()[0]


@pytest.fixture(scope="module")
def toy(tmp_path_factory):
    view = SchemaView(TOY_SCHEMA)
    view.merge_imports()
    connection = create_database(generate_ddl(view))
    ddl_tables = set(table_columns(connection))
    report = load_rows(connection, view, TOY_ROWS)
    drop_empty_link_tables(connection, view)
    dangling = dangling_references(connection)
    searchable = enable_search(connection, view, report)
    path = tmp_path_factory.mktemp("browse") / "toy.sqlite"
    save(connection, path)
    metadata = database_metadata(connection, view, "The toy data.")
    yield {
        "view": view,
        "connection": connection,
        "ddl_tables": ddl_tables,
        "report": report,
        "dangling": dangling,
        "searchable": searchable,
        "path": path,
        "metadata": metadata,
    }
    connection.close()


def test_open_ranges_are_text_and_the_tree_root_has_no_table(toy):
    schema = table_schema(toy["view"])
    assert "Box" not in schema.classes and "Any" not in schema.classes
    assert schema.slots["seeAlso"].range == "string"
    columns = table_columns(toy["connection"])
    assert "seeAlso" in columns["Thing"] and "Box_id" not in columns["Thing"]
    foreign = toy["connection"].execute('pragma foreign_key_list("Thing")').fetchall()
    assert foreign == []


def test_each_record_is_in_its_class_table_and_every_ancestor_table(toy):
    connection = toy["connection"]
    assert count(connection, "Part") == 3 and count(connection, "Kit") == 1
    # The abstract parents hold their subclasses' records: Group the kit, Thing all four.
    assert count(connection, "Group") == 1
    assert count(connection, "Thing") == 4
    assert toy["report"].refused == {} and toy["report"].unplaced == {}


def test_a_reference_to_an_abstract_parent_resolves(toy):
    connection = toy["connection"]
    joined = connection.execute(
        'select p.id, g.name from "Part" p join "Group" g on g.id = p."partOf" order by p.id'
    ).fetchall()
    assert joined == [("p1", "Starter kit"), ("p2", "Starter kit")]
    # The third part names a kit the data does not hold, and the build says so.
    assert toy["dangling"] == {("Part", "Group"): 1}


def test_multivalued_slots_fill_link_tables_and_empty_ones_are_dropped(toy):
    connection = toy["connection"]
    assert count(connection, "Part_aliases") == 3
    # The parent's link table holds the same values, so its rows link out as well.
    assert count(connection, "Thing_aliases") == 3
    assert connection.execute('select * from "Part_related"').fetchall() == [("p1", "p2")]
    tables = set(table_columns(connection))
    assert {"Gadget_aliases", "Kit_aliases", "Group_aliases"} <= toy["ddl_tables"] - tables
    # Every class table stays, empty or not, so every foreign key keeps its parent.
    assert "Gadget" in tables


def test_search_finds_a_record_by_a_word_of_its_name(toy):
    assert {"Part", "Thing", "Kit", "Group"} <= set(toy["searchable"])
    found = toy["connection"].execute(
        'select id from "Part" where rowid in '
        '(select rowid from "Part_fts" where "Part_fts" match ?)',
        ("copper",),
    ).fetchall()
    assert found == [("p1",)]


def test_metadata_describes_tables_hides_empty_ones_and_offers_facets(toy):
    tables = toy["metadata"]["tables"]
    assert tables["Gadget"] == {"hidden": True}
    part = tables["Part"]
    assert part["description"] == "One part."
    assert part["label_column"] == "name"
    assert set(part["facets"]) == {"partOf", "size"}
    assert part["columns"]["partOf"] == "The group the part belongs to."
    assert "Part" in tables["Part_aliases"]["description"]
    assert not any(entry.get("hidden") for name, entry in tables.items() if name != "Gadget")


def test_datasette_links_a_reference_to_the_parent_row_and_back(toy):
    async def get(*paths: str):
        datasette = Datasette(
            [str(toy["path"])], metadata={"databases": {"toy": toy["metadata"]}}
        )
        return [await datasette.client.get(path) for path in paths]

    table, row = asyncio.run(get("/toy/Part", "/toy/Group/k1"))
    assert table.status_code == row.status_code == 200
    # The part's reference is shown by the kit's label and links to the kit's row in the
    # abstract parent's table, which is where the reference points.
    assert '<a href="/toy/Group/k1">Starter kit</a>' in table.text
    # That row page lists the parts that point at it.
    assert "from partOf in Part" in row.text


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    from lib.browse.loader import build_all

    data_dir = tmp_path_factory.mktemp("browse-data")
    return data_dir, build_all(data_dir, which=(False, True))


@pytest.fixture(scope="module")
def library_rows():
    from lib.store.loader import load_container, rows_by_class

    return rows_by_class(load_container(byod=False))


@pytest.mark.slow
def test_each_class_table_holds_the_library_count_of_its_class(built, library_rows):
    from lib.api.exposure import schema_view

    view = schema_view()
    data_dir, _ = built
    with sqlite3.connect(data_dir / "atlas.sqlite") as connection:
        for class_name in library_rows:
            expected = sum(
                len(records)
                for other, records in library_rows.items()
                if class_name in view.class_ancestors(other)
            )
            assert count(connection, class_name) == expected, class_name


@pytest.mark.slow
def test_a_reference_to_an_abstract_parent_resolves_in_the_data(built):
    from lib.api.exposure import schema_view

    view = schema_view()
    target = view.induced_slot("isDefinedByTaxonomy", "Risk").range
    assert view.get_class(target).abstract
    data_dir, _ = built
    with sqlite3.connect(data_dir / "atlas.sqlite") as connection:
        (values,) = connection.execute(
            'select count(*) from "Risk" where "isDefinedByTaxonomy" is not null'
        ).fetchone()
        kinds = dict(
            connection.execute(
                f'select t.type, count(*) from "Risk" r join "{target}" t '
                'on t.id = r."isDefinedByTaxonomy" group by t.type'
            ).fetchall()
        )
    assert values and sum(kinds.values()) == values
    # The rows the references reach are subclass records, there only as ancestor rows.
    assert "RiskTaxonomy" in kinds


@pytest.mark.slow
def test_search_finds_a_known_risk_by_a_word_of_its_name(built):
    data_dir, _ = built
    with sqlite3.connect(data_dir / "atlas.sqlite") as connection:
        found = {
            row[0]
            for row in connection.execute(
                'select id from "Risk" where rowid in '
                '(select rowid from "Risk_fts" where "Risk_fts" match ?)',
                ("toxic",),
            )
        }
    assert "atlas-toxic-output" in found


@pytest.mark.slow
def test_empty_tables_are_hidden_and_full_ones_are_described(built):
    from lib.browse.metadata import search_tables

    data_dir, _ = built
    metadata = yaml.safe_load((data_dir / "metadata.yaml").read_text(encoding="utf-8"))
    for alias in ("atlas", "byod"):
        tables = metadata["databases"][alias]["tables"]
        with sqlite3.connect(data_dir / f"{alias}.sqlite") as connection:
            searchable = search_tables(connection)
            counts = {
                table: count(connection, table)
                for table in table_columns(connection)
                if table not in searchable
            }
        full = [table for table, rows in counts.items() if rows]
        empty = [table for table, rows in counts.items() if not rows]
        assert empty and all(tables[table].get("description") is not None for table in full)
        assert not any(tables[table].get("hidden") for table in full)
        for table in empty:
            # Datasette hides a table whose name starts with a hidden table's name, so an
            # empty table whose name begins a full one's is the one exception.
            shadows = any(other.startswith(table) for other in full)
            assert tables.get(table) == ({"hidden": True} if not shadows else None), table


@pytest.mark.slow
def test_the_byod_database_holds_more_rows_than_the_packaged_one(built):
    _, build = built
    atlas, byod = build.databases
    assert byod.load.records > atlas.load.records
    assert byod.load.link_rows > atlas.load.link_rows


@pytest.mark.slow
def test_datasette_serves_the_built_directory_as_just_browse_does(built):
    data_dir, _ = built

    async def get(path: str):
        datasette = Datasette(config_dir=data_dir)
        return await datasette.client.get(path)

    response = asyncio.run(get("/atlas/Risk.json?_search=toxic&_shape=array&_labels=on"))
    assert response.status_code == 200
    toxic = next(row for row in response.json() if row["id"] == "atlas-toxic-output")
    # The taxonomy reference comes with the taxonomy's name as its label.
    assert toxic["isDefinedByTaxonomy"]["label"]
