"""The Cypher export is fetched from ai-atlas-nexus, not generated here.

These tests cover ``scripts/fetch_cypher.py`` and the ``export`` branch of ``handlers.graph``.
Everything but the last test runs offline by replacing ``urllib.request.urlopen`` in the
script's module with a small fake; the last test reaches GitHub and is marked ``slow``.
"""

from __future__ import annotations

import datetime as dt
import io
import urllib.error
import urllib.request

import pytest
import requests

from scripts import fetch_cypher

FAKE_BODY = b'MERGE (node:Risk {id: "example"}) ON CREATE SET node += {name: "Example"};\n'


class _FakeResponse(io.BytesIO):
    """The parts of an HTTP response that ``fetch`` uses: ``read`` and the context manager."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def _serve(monkeypatch, body: bytes = FAKE_BODY):
    """Make ``urlopen`` answer with ``body`` and record each URL it was asked for."""
    calls: list[str] = []

    def fake_urlopen(request, timeout=None):
        calls.append(request.full_url)
        return _FakeResponse(body)

    monkeypatch.setattr(fetch_cypher.urllib.request, "urlopen", fake_urlopen)
    return calls


def _serve_404(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", hdrs=None, fp=None)

    monkeypatch.setattr(fetch_cypher.urllib.request, "urlopen", fake_urlopen)


def test_artefact_url_pins_the_release_tag():
    expected = (
        "https://raw.githubusercontent.com/IBM/ai-atlas-nexus/v1.2.5/"
        "graph_export/cypher/ai-risk-ontology.cypher"
    )
    assert fetch_cypher.artefact_url("1.2.5") == expected
    assert fetch_cypher.artefact_url("v1.2.5") == expected


def test_provenance_header_is_three_cypher_comments():
    url = fetch_cypher.artefact_url("1.2.5")
    header = fetch_cypher.provenance_header(url, "1.2.5", dt.date(2026, 10, 10))
    assert header.splitlines() == [
        f"// source: {url}",
        "// ai-atlas-nexus: 1.2.5",
        "// fetched: 2026-10-10",
    ]


def test_fetch_writes_header_then_body(tmp_path, monkeypatch):
    calls = _serve(monkeypatch)
    output = tmp_path / "ai-risk-ontology.cypher"
    path = fetch_cypher.fetch(version="1.2.5", output=output)
    assert path == output
    assert calls == [fetch_cypher.artefact_url("1.2.5")]
    text = output.read_bytes()
    header, body = text[: len(text) - len(FAKE_BODY)], text[len(text) - len(FAKE_BODY):]
    assert body == FAKE_BODY
    assert header.decode().startswith("// source: ")
    assert fetch_cypher.recorded_version(output) == "1.2.5"
    assert not list(tmp_path.glob("*.part"))


def test_fetch_skips_when_the_same_version_is_recorded(tmp_path, monkeypatch):
    calls = _serve(monkeypatch)
    output = tmp_path / "ai-risk-ontology.cypher"
    fetch_cypher.fetch(version="1.2.5", output=output)
    fetch_cypher.fetch(version="1.2.5", output=output)
    assert len(calls) == 1
    fetch_cypher.fetch(version="1.2.6", output=output)
    fetch_cypher.fetch(version="1.2.6", output=output, force=True)
    assert len(calls) == 3


def test_missing_tag_is_a_clear_error(tmp_path, monkeypatch, capsys):
    _serve_404(monkeypatch)
    output = tmp_path / "ai-risk-ontology.cypher"
    with pytest.raises(fetch_cypher.FetchError) as excinfo:
        fetch_cypher.fetch(version="9.9.9", output=output)
    assert "v9.9.9" in str(excinfo.value)
    assert not output.exists()
    assert fetch_cypher.main([str(output), "--version", "v9.9.9"]) == 1
    assert "v9.9.9" in capsys.readouterr().err


def test_non_cypher_response_is_refused(tmp_path, monkeypatch):
    _serve(monkeypatch, body=b"<!doctype html><title>Not Cypher</title>")
    output = tmp_path / "ai-risk-ontology.cypher"
    with pytest.raises(fetch_cypher.FetchError):
        fetch_cypher.fetch(version="1.2.5", output=output)
    assert not output.exists()
    assert not list(tmp_path.glob("*.part"))


def test_byod_with_cypher_export_is_refused_in_the_handler():
    from fastapi import HTTPException

    from lib.api.handlers import graph

    with pytest.raises(HTTPException) as excinfo:
        graph(export=True, id="cypher", byod=True)
    assert excinfo.value.status_code == 400
    assert "byo/data" in excinfo.value.detail


def test_byod_with_cypher_export_is_400_over_http(api_server: str):
    response = requests.get(
        f"{api_server}/graph",
        params={"export": "true", "id": "cypher", "byod": "true"},
        timeout=10,
    )
    assert response.status_code == 400, response.text
    assert "byo/data" in response.json()["detail"]


def _online(url: str) -> bool:
    try:
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError):
        return False


@pytest.mark.slow
def test_installed_version_has_an_artefact_upstream(tmp_path):
    """The tag for the installed ai-atlas-nexus carries the Cypher export, and it loads as such."""
    version = fetch_cypher.installed_version()
    url = fetch_cypher.artefact_url(version)
    if not _online(url):
        pytest.skip(f"offline, or {url} is not reachable")
    output = tmp_path / "ai-risk-ontology.cypher"
    fetch_cypher.fetch(version=version, output=output)
    with output.open("rb") as handle:
        lines = [handle.readline() for _ in range(4)]
    assert lines[1] == f"// ai-atlas-nexus: {version}\n".encode()
    assert lines[3].startswith(b"MERGE")
    assert output.stat().st_size > 1_000_000
