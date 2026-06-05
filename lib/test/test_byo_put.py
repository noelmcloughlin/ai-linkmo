"""Security tests for the PUT /byo/{filename} upload endpoint.

These tests exercise the hardening added in `lib.api.handlers._safe_byo_path`
and `byo_put`: path traversal, disallowed suffixes, oversize bodies, and
malformed YAML must all fail closed.
"""

from __future__ import annotations

import io

import pytest
import requests


@pytest.mark.parametrize(
    "filename",
    [
        "../etc/passwd",
        "..\\evil.yaml",
        "/absolute.yaml",
        ".",
        "..",
        "",
    ],
)
def test_byo_put_rejects_path_traversal(api_server: str, filename: str) -> None:
    """Reject filenames that try to escape byo/data/."""
    response = requests.put(
        f"{api_server}/byo",
        params={"filename": filename},
        data=b"taxonomy: {}\n",
        timeout=5,
    )
    assert response.status_code == 400, response.text


@pytest.mark.parametrize("filename", ["evil.exe", "notes.txt", "noext"])
def test_byo_put_rejects_bad_suffix(api_server: str, filename: str) -> None:
    """Only YAML extensions are accepted."""
    response = requests.put(
        f"{api_server}/byo",
        params={"filename": filename},
        data=b"taxonomy: {}\n",
        timeout=5,
    )
    assert response.status_code == 400, response.text


def test_byo_put_rejects_oversize_payload(api_server: str) -> None:
    """Bodies larger than the server cap return 413, not 200."""
    # 11 MiB - one byte above the 10 MiB cap configured in handlers.py.
    oversized = b"a" * (10 * 1024 * 1024 + 1)
    response = requests.put(
        f"{api_server}/byo",
        params={"filename": "oversized.yaml"},
        data=oversized,
        headers={"content-length": str(len(oversized))},
        timeout=10,
    )
    assert response.status_code == 413, response.text


def test_byo_put_rejects_malformed_yaml(api_server: str) -> None:
    """A YAML parse error must roll back and respond 400."""
    bad_yaml = b"{ not: valid: yaml :: ["
    response = requests.put(
        f"{api_server}/byo",
        params={"filename": "_pytest_invalid.yaml"},
        data=io.BytesIO(bad_yaml),
        timeout=5,
    )
    assert response.status_code == 400, response.text
