"""The questions in expected_counts.yaml get the counts written there.

The table belongs to this project. Fill it in as the data becomes stable. Each case runs
through the command line in local mode and through the API, and both must give its count.
A case may also say how many records the datamodel rejected, as ``validation_errors``.
"""

from __future__ import annotations

import pytest
from linkmo_cases import case_id, load_cases, to_query

from ai_risk_ontology_linkmo.output import count_of

CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=case_id)
def test_the_count_is_the_expected_one(exposure, cli, client, runner, case):
    result = runner.invoke(cli, [*map(str, case["args"]), "--count", "--mode", "local"])
    assert result.exit_code == 0, result.output
    assert int(result.stdout.strip()) == case["count"]
    path, params = to_query(exposure, case["args"])
    body = client.get(path, params=params).json()
    assert count_of(body) == case["count"]
    if "validation_errors" in case:
        assert len(body["validation_errors"]) == case["validation_errors"], body["validation_errors"]


def test_the_table_has_cases():
    if not CASES:
        pytest.skip("tests/expected_counts.yaml has no cases yet")
