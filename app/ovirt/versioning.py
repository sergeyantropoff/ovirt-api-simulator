"""Resolve Engine API version (v3/v4) and active series pack."""

from __future__ import annotations

import re
from dataclasses import dataclass

from fastapi import Request

from app.ovirt.errors import OVirtError

_VERSION_PREFIX = re.compile(r"^/ovirt-engine/api/(v[34])(/.*)?$")


@dataclass(frozen=True)
class ApiVersionContext:
    api_version: str  # "3" or "4"
    series: str
    path_suffix: str  # path after /ovirt-engine/api[/vN]


def resolve_api_version(request: Request, default_series: str = "4.5") -> ApiVersionContext:
    path = request.url.path
    header = (request.headers.get("version") or "").strip()
    series = getattr(request.app.state, "ovirt_series", None) or default_series

    m = _VERSION_PREFIX.match(path)
    if m:
        ver = m.group(1)[1:]  # strip v
        rest = m.group(2) or ""
        return ApiVersionContext(api_version=ver, series=series, path_suffix=rest or "/")

    if path.startswith("/ovirt-engine/api"):
        rest = path[len("/ovirt-engine/api") :] or "/"
        if header in {"3", "4"}:
            return ApiVersionContext(api_version=header, series=series, path_suffix=rest)
        # default version 4 for 4.x series, 3 for 3.x
        default = "3" if str(series).startswith("3.") else "4"
        return ApiVersionContext(api_version=default, series=series, path_suffix=rest)

    raise OVirtError("NotFound", f"Unknown path {path}", status_code=404)


def strip_api_prefix(path: str) -> str:
    """Normalize to collection-relative path starting with /."""

    for prefix in (
        "/ovirt-engine/api/v4",
        "/ovirt-engine/api/v3",
        "/ovirt-engine/api",
    ):
        if path.startswith(prefix):
            rest = path[len(prefix) :] or "/"
            return rest if rest.startswith("/") else f"/{rest}"
    return path
