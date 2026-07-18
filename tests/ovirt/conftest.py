"""Shared fixtures for live Engine API tests."""

from __future__ import annotations

import os

import pytest
import requests


def discover_base_url() -> str:
    for candidate in (
        os.environ.get("OVIRT_TEST_URL"),
        "https://api-gateway",
        "https://127.0.0.1",
        "https://127.0.0.1:9443",
    ):
        if not candidate:
            continue
        try:
            r = requests.get(f"{candidate.rstrip('/')}/health/live", timeout=3, verify=False)
            if r.status_code == 200:
                return candidate.rstrip("/")
        except Exception:
            continue
    pytest.skip("no running oVirt simulator gateway")


def oauth_token(base: str, username: str = "admin@internal", password: str = "secret") -> str:
    r = requests.post(
        f"{base}/ovirt-engine/sso/oauth/token",
        data={
            "grant_type": "password",
            "username": username,
            "password": password,
            "scope": "ovirt-app-api",
        },
        verify=False,
        timeout=60,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth_headers(token: str, *, version: str = "4") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Version": version,
    }


def collection_items(body: dict, element: str) -> list[dict]:
    """Normalize Engine JSON list/single-entity payloads to a list."""

    raw = body.get(element)
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return [raw]
    return []


@pytest.fixture(scope="module")
def base_url() -> str:
    return discover_base_url()


@pytest.fixture(scope="module")
def token(base_url: str) -> str:
    return oauth_token(base_url)
