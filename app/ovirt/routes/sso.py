"""oVirt Engine SSO OAuth2 endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from app.ovirt.auth import issue_oauth_token
from app.ovirt.deps import get_db
from app.ovirt.errors import OVirtError
from app.ovirt.settings import OPT_DEFAULT_API_SCOPE, option_value

router = APIRouter(tags=["sso"])


@router.post("/ovirt-engine/sso/oauth/token")
async def oauth_token(
    request: Request,
    grant_type: str = Form(default=""),
    username: str = Form(default=""),
    password: str = Form(default=""),
    scope: str = Form(default=""),
) -> JSONResponse:
    if grant_type and grant_type != "password":
        raise OVirtError("BadRequest", f"Unsupported grant_type: {grant_type}", status_code=400)
    if not username:
        try:
            body = await request.json()
        except Exception:
            body = {}
        username = str(body.get("username") or "")
        password = str(body.get("password") or "")
        scope = str(body.get("scope") or scope or "")
        grant_type = str(body.get("grant_type") or grant_type or "password")
    if not username or not password:
        raise OVirtError("Unauthorized", "username and password required", status_code=401)
    db = get_db(request)
    async with db.pool.acquire() as conn:
        if not scope:
            scope = await option_value(conn, OPT_DEFAULT_API_SCOPE)
        token = await issue_oauth_token(
            conn, username=username, password=password, scope=scope
        )
    return JSONResponse(token)


@router.get("/ovirt-engine/sso/oauth/token-info")
async def token_info(request: Request) -> JSONResponse:
    from app.ovirt.auth import resolve_request_auth

    db = get_db(request)
    async with db.pool.acquire() as conn:
        ctx = await resolve_request_auth(conn, dict(request.headers))
        row = await conn.fetchrow(
            "SELECT scope, revoked, expires_at FROM ov_tokens WHERE id=$1", ctx.token_id
        )
    active = bool(row) and not row["revoked"]
    return JSONResponse(
        {
            "active": active,
            "user_id": str(ctx.user_id),
            "user_name": f"{ctx.user_name}@{ctx.domain}",
            "exp": int(ctx.expires_at.timestamp()),
            "scope": (row["scope"] if row else ctx.scope),
        }
    )


@router.post("/ovirt-engine/sso/oauth/revoke")
async def revoke_token(request: Request) -> JSONResponse:
    from app.ovirt.auth import extract_auth

    db = get_db(request)
    kind = extract_auth(dict(request.headers))
    token = None
    if kind and kind[0] in {"bearer", "session"}:
        token = kind[1]
    else:
        form = await request.form()
        token = str(form.get("token") or "")
    result = "missing"
    if token:
        async with db.pool.acquire() as conn:
            updated = await conn.fetchval(
                """UPDATE ov_tokens SET revoked=true WHERE id=$1
                   RETURNING id""",
                token,
            )
            result = "ok" if updated else "not_found"
    return JSONResponse({"result": result})
