"""Register each Engine contract operation as its own FastAPI route."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.api.openapi import contract_openapi_tags
from app.ovirt.opspec import OperationSpec, SeriesPack

Endpoint = Callable[[Request], Awaitable[Response]]
_NON_ALNUM = re.compile(r"[^a-zA-Z0-9_]+")


def clear_ovirt_contract_routes(app: FastAPI) -> None:
    """Drop contract + Engine fallback routes before a remount."""

    app.router.routes = [
        route for route in app.router.routes if not _is_swappable_ovirt_route(route)
    ]
    app.openapi_schema = None


def register_ovirt_contract_routes(app: FastAPI, pack: SeriesPack) -> int:
    """Register one FastAPI route per contract operation.

    Paths are taken from the pack as-is (including ``/v3`` / ``/v4`` variants).
    Returns the number of routes added.
    """

    seen: set[tuple[str, str]] = set()
    registered = 0
    for op in pack.operations:
        method = op.method.upper()
        path = _normalize_route_path(op.path)
        key = (path, method)
        if key in seen:
            continue
        seen.add(key)
        app.add_api_route(
            path,
            _endpoint_for(op),
            methods=[method],
            name=f"contract:{method}:{path}",
            tags=cast(list[str | Enum], contract_openapi_tags(path)),
            summary=op.notes or op.operation_id,
            operation_id=_unique_operation_id(op, method, path),
            openapi_extra={
                "x-ovirt-operation-id": op.operation_id,
                "x-ovirt-series": pack.series,
                "x-ovirt-kind": op.kind,
            },
        )
        registered += 1
    app.openapi_schema = None
    return registered


def _is_swappable_ovirt_route(route: object) -> bool:
    name = getattr(route, "name", None)
    return isinstance(name, str) and (
        name.startswith("contract:") or name.startswith("ovirt-fallback:")
    )


def _unique_operation_id(op: OperationSpec, method: str, path: str) -> str:
    """Build a unique OpenAPI operationId (packs repeat ids across /v3|/v4)."""

    base = op.operation_id.replace(".", "_")
    suffix = _NON_ALNUM.sub("_", f"{method}_{path}").strip("_")
    return f"{base}__{suffix}"


def _normalize_route_path(path: str) -> str:
    """Ensure FastAPI path template form (leading slash, no trailing slash except root)."""

    cleaned = path.strip() or "/"
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    if cleaned != "/" and cleaned.endswith("/"):
        cleaned = cleaned.rstrip("/")
    return cleaned


def _endpoint_for(op: OperationSpec) -> Endpoint:
    async def dispatch(request: Request) -> Response:
        from app.ovirt.routes.engine import handle_engine_request

        return await handle_engine_request(request)

    dispatch.__name__ = f"contract_{op.operation_id.replace('.', '_')}"
    dispatch.__doc__ = op.notes or op.operation_id
    return dispatch
