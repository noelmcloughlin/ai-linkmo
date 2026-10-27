"""Unit tests for `ai_linkmo.cli.api_base_url`.

The resolver decides which API base URL the CLI will trust by default. It
must accept local hosts unconditionally and require an explicit opt-in for
anything else, otherwise an exfiltrated env var could silently redirect
every CLI query to an attacker-controlled server.
"""

from __future__ import annotations

import pytest

from ai_linkmo.cli import api_base_url


@pytest.fixture
def resolver(monkeypatch: pytest.MonkeyPatch):
    """The resolver, with neither variable set. It reads them on each call."""
    monkeypatch.delenv("AI_LINKMO_API_URL", raising=False)
    monkeypatch.delenv("AI_LINKMO_API_URL_ALLOW_REMOTE", raising=False)
    return api_base_url


def test_unset_returns_default(resolver) -> None:
    assert resolver() == "http://localhost:8000"


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000",
        "http://127.0.0.1:9001",
        "http://[::1]:8000",
    ],
)
def test_local_hosts_accepted(monkeypatch: pytest.MonkeyPatch, resolver, url: str) -> None:
    monkeypatch.setenv("AI_LINKMO_API_URL", url)
    assert resolver() == url


@pytest.mark.parametrize(
    "url",
    [
        "not-a-url",
        "ftp://localhost:8000",
        "://broken",
        "http://",
    ],
)
def test_malformed_urls_fall_back(monkeypatch: pytest.MonkeyPatch, resolver, url: str) -> None:
    monkeypatch.setenv("AI_LINKMO_API_URL", url)
    assert resolver() == "http://localhost:8000"


def test_remote_requires_opt_in(monkeypatch: pytest.MonkeyPatch, resolver) -> None:
    monkeypatch.setenv("AI_LINKMO_API_URL", "http://example.com:8000")
    # No opt-in -> fall back to the safe default.
    assert resolver() == "http://localhost:8000"


def test_remote_accepted_when_opted_in(monkeypatch: pytest.MonkeyPatch, resolver) -> None:
    remote = "https://api.example.com"
    monkeypatch.setenv("AI_LINKMO_API_URL", remote)
    monkeypatch.setenv("AI_LINKMO_API_URL_ALLOW_REMOTE", "1")
    assert resolver() == remote
