"""Tests of the operations written by hand in src/ai_risk_ontology_linkmo/hand.py.

The linkmo template created this file once and never overwrites it. Change it when you
change the operations it tests.
"""

from __future__ import annotations


def test_summary_counts_every_exposed_class(exposure, client):
    if "/summary" not in exposure.hand_paths:
        return
    body = client.get("/summary").json()
    assert set(body) == set(exposure.by_scope)
    one = next(iter(exposure.by_scope))
    assert client.get("/summary", params={"scope": one}).json() == {one: body[one]}
    assert client.get("/summary", params={"scope": "no-such-command"}).status_code == 404
