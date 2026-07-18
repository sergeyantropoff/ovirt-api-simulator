"""Shared configuration for the Pulumi Engine contract-coverage lab."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str | None = None, *, allow_empty: bool = False) -> str:
    value = os.environ.get(name, default)
    if value is None or (value == "" and not allow_empty and default is None):
        raise RuntimeError(f"required environment variable {name} is not set")
    return value if value is not None else ""


@dataclass(frozen=True)
class SuiteConfig:
    api_url: str
    api_base: str
    sso_base: str
    user: str
    password: str
    verify_tls: bool
    timeout_seconds: float
    contracts_root: str
    series_filter: str
    methods_filter: str
    smoke_only: bool
    report_dir: str

    @classmethod
    def from_env(cls) -> SuiteConfig:
        api_url = _env("OVIRT_URL", "https://api-gateway").rstrip("/")
        return cls(
            api_url=api_url,
            api_base=f"{api_url}/ovirt-engine/api",
            sso_base=f"{api_url}/ovirt-engine/sso/oauth",
            user=_env("OVIRT_USER", "admin@internal"),
            password=_env("OVIRT_PASSWORD", "secret"),
            verify_tls=_env("OVIRT_VERIFY_TLS", "0") == "1",
            timeout_seconds=float(_env("OVIRT_TIMEOUT", "60")),
            contracts_root=_env("OVIRT_CONTRACTS_ROOT", "/contracts/ovirt"),
            series_filter=_env("OVIRT_SERIES_FILTER", "", allow_empty=True).strip(),
            methods_filter=_env("OVIRT_METHODS_FILTER", "", allow_empty=True).strip().upper(),
            smoke_only=_env("SMOKE_ONLY", "0") == "1",
            report_dir=_env("REPORT_DIR", "/workspace/reports"),
        )
