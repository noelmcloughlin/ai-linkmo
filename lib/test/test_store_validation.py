"""The validation step reports a planted bad row, and only that row, from linkml-store's findings.

The store is the loader's full build of the packaged data, which takes about seven seconds.
Validation is then run through a config that declares only the three collections the
planted rows involve, because linkml-store's referential pass costs one query per
single-valued reference (about 60 ms each here) and the whole database would take four
minutes a pass. ``Risk`` alone still means 630 lookups, so one pass serves every assertion.
"""

from __future__ import annotations

import json

import pytest

from lib.store.loader import build_database, open_database, write_config
from scripts.validate_store import REFERENTIAL, main

DANGLING_RISK = {
    "id": "test-dangling-risk",
    "name": "Risk defined by a taxonomy that does not exist",
    "isDefinedByTaxonomy": "no-such-taxonomy",
}
BAD_STATUS_RISK = {
    "id": "test-bad-status-risk",
    "name": "Risk with a lifecycle status outside the enum",
    "hasLifecycleStatus": "not-a-status",
}


@pytest.fixture(scope="module")
def validated(tmp_path_factory):
    """Build the store, plant the two bad rows, validate once, and hand back the result."""
    data_dir = tmp_path_factory.mktemp("store")
    counts = build_database(byod=False, data_dir=data_dir)
    database = open_database(byod=False, data_dir=data_dir)
    try:
        database.get_collection("Risk").insert([DANGLING_RISK, BAD_STATUS_RISK])
        database.commit()
    finally:
        database.close()
    # A Taxonomy-ranged reference is looked up in the Taxonomy collection; RiskTaxonomy is
    # declared too so that the script's subclass resolution has somewhere to look.
    subset = {name: counts[name] for name in ("Risk", "Taxonomy", "RiskTaxonomy")}
    config = write_config({"atlas": subset}, data_dir)
    output = data_dir / "findings.json"
    exit_code = main([str(config), "--output", str(output), "--allow", "0"])
    return data_dir, counts, exit_code, json.loads(output.read_text())


def test_dangling_reference_is_exactly_one_referential_finding(validated):
    _, _, _, findings = validated
    about_reference = [
        f for f in findings if f["instance"] == DANGLING_RISK["isDefinedByTaxonomy"]
    ]
    assert [f["type"] for f in about_reference] == [REFERENTIAL]
    assert about_reference[0]["collection"] == "Taxonomy"
    assert about_reference[0]["severity"] == "ERROR"
    # The planted row is otherwise valid, so nothing else is said about it.
    assert not [f for f in findings if f["instance"] == DANGLING_RISK["id"]]


def test_bad_enum_value_is_a_jsonschema_finding(validated):
    _, _, _, findings = validated
    about_row = [f for f in findings if f["instance"] == BAD_STATUS_RISK["id"]]
    assert [f["type"] for f in about_row] == ["jsonschema validation"]
    assert about_row[0]["collection"] == "Risk"
    assert "not-a-status" in about_row[0]["message"]
    assert "hasLifecycleStatus" in about_row[0]["message"]


def test_findings_beyond_allow_exit_one_and_are_in_order(validated):
    _, _, exit_code, findings = validated
    assert exit_code == 1
    keys = [
        (f["database"], f["collection"], f["type"], f["instance"], f["message"])
        for f in findings
    ]
    assert keys == sorted(keys)


def test_clean_collection_within_allow_exits_zero(validated, capsys):
    data_dir, counts, _, _ = validated
    config = write_config({"atlas": {"RiskTaxonomy": counts["RiskTaxonomy"]}}, data_dir)
    assert main([str(config), "--database", "atlas"]) == 0
    assert capsys.readouterr().out.splitlines()[-2:] == [
        "atlas: 0 findings (none)",
        "total 0 findings, allowed 0",
    ]
