"""Mount oVirt Engine API + SSO onto the FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI

from app.ovirt.contract_loader import ensure_loaded
from app.ovirt.errors import OVirtError, ovirt_error_handler
from app.ovirt.registry import register_ovirt_contract_routes
from app.ovirt.routes import engine, sso


def mount_ovirt_routes(app: FastAPI, *, series: str = "4.5") -> None:
    """Register Engine REST API, SSO, and load the active series pack.

    Contract operations are registered as individual OpenAPI routes.
    Catch-all handlers remain as a hidden fallback.
    """

    app.add_exception_handler(OVirtError, ovirt_error_handler)
    app.include_router(sso.router)

    rt = ensure_loaded(series)
    try:
        summary = rt.reload(series)
    except FileNotFoundError:
        summary = {"operation_count": 0, "series": series}
    registered = 0
    if rt.pack is not None:
        registered = register_ovirt_contract_routes(app, rt.pack)

    # Fallback catch-all after specific contract routes (first match wins).
    app.include_router(engine.router)

    app.state.ovirt_series = series
    app.state.ovirt_schema_ops = registered or summary.get("operation_count", 0)
    app.state.runtime_version = f"ovirt-{series}"
