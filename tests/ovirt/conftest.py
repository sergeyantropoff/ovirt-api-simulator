"""Shared fixtures for live Engine API tests."""

from __future__ import annotations

import os

import pytest
import requests


def discover_base_url() -> str:
    """Prefer OVIRT_TEST_URL / OVIRT_ENGINE_PORT; require Engine SSO path (not a foreign :443)."""

    port = (os.environ.get("OVIRT_ENGINE_PORT") or "").strip()
    candidates: list[str] = []
    if os.environ.get("OVIRT_TEST_URL"):
        candidates.append(os.environ["OVIRT_TEST_URL"].rstrip("/"))
    candidates.append("https://api-gateway")
    if port and port != "443":
        candidates.append(f"https://127.0.0.1:{port}")
    candidates.extend(
        [
            "https://127.0.0.1:7443",
            "https://127.0.0.1:6443",
            "https://127.0.0.1",
            "https://127.0.0.1:9443",
        ]
    )
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            live = requests.get(f"{candidate}/health/live", timeout=3, verify=False)
            if live.status_code != 200:
                continue
            # Distinguish this lab from other listeners on :443.
            probe = requests.get(
                f"{candidate}/ovirt-engine/api/",
                headers={"Accept": "application/json"},
                timeout=3,
                verify=False,
            )
            if probe.status_code in {200, 401}:
                return candidate
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
