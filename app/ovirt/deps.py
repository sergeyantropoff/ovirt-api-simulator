"""FastAPI dependencies for oVirt routes."""

from __future__ import annotations

from fastapi import Request

from app.db.pool import AsyncpgDatabase
from app.ovirt.auth import AuthContext, resolve_request_auth
from app.ovirt.errors import OVirtError


def get_db(request: Request) -> AsyncpgDatabase:
    db = getattr(request.app.state, "database", None)
    if db is None:
        raise OVirtError("ServiceUnavailable", "Database not ready", status_code=503)
    return db  # type: ignore[return-value]


async def require_auth(request: Request) -> AuthContext:
    db = get_db(request)
    async with db.pool.acquire() as conn:
        return await resolve_request_auth(conn, dict(request.headers))
