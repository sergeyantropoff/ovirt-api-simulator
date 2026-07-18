"""oVirt Engine SSO OAuth2 + Basic auth + session cookies."""

from __future__ import annotations

import base64
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from asyncpg import Connection

from app.ovirt.errors import OVirtError
from app.ovirt.settings import (
    OPT_BASIC_SESSION_TTL_SECONDS,
    OPT_DEFAULT_API_SCOPE,
    OPT_DEFAULT_AUTH_DOMAIN,
    OPT_DEFAULT_TOKEN_TYPE,
    OPT_DEFAULT_USER_ROLE,
    OPT_OAUTH_TOKEN_TTL_SECONDS,
    option_int,
    option_value,
)
from app.security.auth import verify_secret


@dataclass(frozen=True)
class AuthContext:
    token_id: str
    user_id: UUID
    user_name: str
    domain: str
    roles: tuple[str, ...]
    expires_at: datetime
    is_admin: bool
    scope: str


async def authenticate_password(
    conn: Connection,
    username: str,
    password: str,
) -> dict[str, Any]:
    """Resolve user@domain credentials."""

    name, _, domain = username.partition("@")
    if not domain:
        domain = await option_value(conn, OPT_DEFAULT_AUTH_DOMAIN)
    row = await conn.fetchrow(
        """SELECT u.id, u.name, u.password_hash, u.enabled, d.name AS domain_name
           FROM ov_users u
           JOIN ov_domains d ON d.id = u.domain_id
           WHERE u.name = $1 AND d.name = $2""",
        name,
        domain,
    )
    if row is None or not row["enabled"] or not verify_secret(password, row["password_hash"]):
        raise OVirtError("Unauthorized", "Incorrect credentials", status_code=401)
    return dict(row)


async def issue_oauth_token(
    conn: Connection,
    *,
    username: str,
    password: str,
    scope: str | None = None,
    ttl_seconds: int | None = None,
) -> dict[str, Any]:
    default_scope = await option_value(conn, OPT_DEFAULT_API_SCOPE)
    token_type = await option_value(conn, OPT_DEFAULT_TOKEN_TYPE)
    if ttl_seconds is None:
        ttl_seconds = await option_int(conn, OPT_OAUTH_TOKEN_TTL_SECONDS)
    scope = scope or default_scope
    if scope and default_scope not in scope.split():
        raise OVirtError("Unauthorized", "Invalid scope", status_code=400)
    user = await authenticate_password(conn, username, password)
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    expires = now + timedelta(seconds=ttl_seconds)
    await conn.execute(
        """INSERT INTO ov_tokens(id, user_id, scope, expires_at, issued_at, revoked)
           VALUES($1, $2, $3, $4, $5, false)""",
        token,
        user["id"],
        scope,
        expires,
        now,
    )
    row = await conn.fetchrow("SELECT * FROM ov_tokens WHERE id=$1", token)
    return {
        "access_token": row["id"],
        "token_type": token_type,
        "scope": row["scope"],
        "exp": int(row["expires_at"].timestamp()),
    }


async def validate_bearer(conn: Connection, token: str) -> AuthContext:
    if not token:
        raise OVirtError("Unauthorized", "Authentication required", status_code=401)
    row = await conn.fetchrow(
        """SELECT t.id, t.user_id, t.expires_at, t.revoked, t.scope,
                  u.name AS user_name, d.name AS domain_name
           FROM ov_tokens t
           JOIN ov_users u ON u.id = t.user_id
           JOIN ov_domains d ON d.id = u.domain_id
           WHERE t.id = $1""",
        token,
    )
    if row is None or row["revoked"]:
        raise OVirtError("Unauthorized", "Invalid token", status_code=401)
    expires = row["expires_at"]
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires <= datetime.now(UTC):
        raise OVirtError("Unauthorized", "Token has expired", status_code=401)
    roles = await _roles_for_user(conn, row["user_id"])
    return AuthContext(
        token_id=str(row["id"]),
        user_id=row["user_id"],
        user_name=str(row["user_name"]),
        domain=str(row["domain_name"]),
        roles=roles,
        expires_at=expires,
        is_admin="SuperUser" in roles or "admin" in roles,
        scope=str(row["scope"] or ""),
    )


async def validate_basic(conn: Connection, header_value: str) -> AuthContext:
    try:
        encoded = header_value.split(" ", 1)[1].strip()
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, _, password = decoded.partition(":")
    except Exception as exc:
        raise OVirtError("Unauthorized", "Malformed basic auth", status_code=401) from exc
    user = await authenticate_password(conn, username, password)
    token = secrets.token_urlsafe(24)
    now = datetime.now(UTC)
    ttl = await option_int(conn, OPT_BASIC_SESSION_TTL_SECONDS)
    default_scope = await option_value(conn, OPT_DEFAULT_API_SCOPE)
    expires = now + timedelta(seconds=ttl)
    await conn.execute(
        """INSERT INTO ov_tokens(id, user_id, scope, expires_at, issued_at, revoked)
           VALUES($1, $2, $3, $4, $5, false)
           ON CONFLICT (id) DO NOTHING""",
        token,
        user["id"],
        default_scope,
        expires,
        now,
    )
    row = await conn.fetchrow("SELECT * FROM ov_tokens WHERE id=$1", token)
    roles = await _roles_for_user(conn, user["id"])
    return AuthContext(
        token_id=str(row["id"]),
        user_id=user["id"],
        user_name=str(user["name"]),
        domain=str(user["domain_name"]),
        roles=roles,
        expires_at=row["expires_at"] if row["expires_at"].tzinfo else row["expires_at"].replace(tzinfo=UTC),
        is_admin="SuperUser" in roles or "admin" in roles,
        scope=str(row["scope"] or default_scope),
    )


async def _roles_for_user(conn: Connection, user_id: UUID) -> tuple[str, ...]:
    rows = await conn.fetch(
        """SELECT r.name FROM ov_permissions p
           JOIN ov_roles r ON r.id = p.role_id
           WHERE p.user_id = $1""",
        user_id,
    )
    names = [str(r["name"]) for r in rows]
    if not names:
        default_role = await option_value(conn, OPT_DEFAULT_USER_ROLE)
        exists = await conn.fetchval("SELECT 1 FROM ov_roles WHERE name=$1", default_role)
        if exists:
            names = [default_role]
    return tuple(names)


def extract_auth(headers: dict[str, str]) -> tuple[str, str] | None:
    """Return ('bearer'|'basic'|'session', credential) or None."""

    lower = {k.lower(): v for k, v in headers.items()}
    auth = lower.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return "bearer", auth.split(" ", 1)[1].strip()
    if auth.lower().startswith("basic "):
        return "basic", auth
    session = lower.get("prefer") or ""
    if "jsessionid" in lower:
        return "session", lower["jsessionid"]
    cookie = lower.get("cookie", "")
    for part in cookie.split(";"):
        part = part.strip()
        if part.lower().startswith("jsessionid="):
            return "session", part.split("=", 1)[1]
        if part.lower().startswith("ovirt_token="):
            return "bearer", part.split("=", 1)[1]
    if session.lower().startswith("persistent-auth"):
        return None
    return None


async def resolve_request_auth(conn: Connection, headers: dict[str, str]) -> AuthContext:
    kind = extract_auth(headers)
    if kind is None:
        raise OVirtError("Unauthorized", "Authentication required", status_code=401)
    mode, credential = kind
    if mode == "bearer":
        return await validate_bearer(conn, credential)
    if mode == "basic":
        return await validate_basic(conn, credential)
    if mode == "session":
        return await validate_bearer(conn, credential)
    raise OVirtError("Unauthorized", "Authentication required", status_code=401)
