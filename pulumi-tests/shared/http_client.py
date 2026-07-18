"""httpx client for Engine API + series activation."""

from __future__ import annotations

import base64
from typing import Any

import httpx

from shared.config import SuiteConfig


class OVirtApiError(RuntimeError):
    def __init__(self, method: str, path: str, response: httpx.Response) -> None:
        super().__init__(f"{method} {path} -> {response.status_code} {response.text[:300]}")
        self.method = method
        self.path = path
        self.status_code = response.status_code
        self.response = response


class OVirtClient:
    def __init__(self, cfg: SuiteConfig | None = None, *, api_version: str = "4") -> None:
        self.cfg = cfg or SuiteConfig.from_env()
        self.api_version = api_version
        self._client = httpx.Client(verify=self.cfg.verify_tls, timeout=self.cfg.timeout_seconds)
        self.token: str | None = None

    def __enter__(self) -> OVirtClient:
        self.login()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def login(self) -> str:
        r = self._client.post(
            f"{self.cfg.sso_base}/token",
            data={
                "grant_type": "password",
                "username": self.cfg.user,
                "password": self.cfg.password,
                "scope": "ovirt-app-api",
            },
            headers={"Accept": "application/json"},
        )
        if r.status_code != 200:
            raise OVirtApiError("POST", "/ovirt-engine/sso/oauth/token", r)
        self.token = r.json()["access_token"]
        return self.token

    def headers(self, *, version: str | None = None) -> dict[str, str]:
        if not self.token:
            self.login()
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Version": version or self.api_version,
        }

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = path if path.startswith("http") else f"{self.cfg.api_url}{path}"
        headers = kwargs.pop("headers", None) or self.headers()
        return self._client.request(method, url, headers=headers, **kwargs)

    def activate_series(self, series: str) -> httpx.Response:
        return self._client.post(
            f"{self.cfg.api_url}/ui/api/ovirt/contracts/activate",
            json={"series": series},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

    def basic_probe(self) -> None:
        r = self._client.get(f"{self.cfg.api_url}/health/ready", headers={"Accept": "application/json"})
        if r.status_code != 200:
            raise RuntimeError(f"simulator not ready: {r.status_code}")
