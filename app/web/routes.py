"""Browser console for exercising the oVirt Engine API simulator."""

from __future__ import annotations

from typing import Annotated

from asyncpg import Pool  # type: ignore[import-untyped]
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.db.pool import AsyncpgDatabase
from app.dependencies import get_database
from app.ovirt.demo_datacenter import CLUSTER_SIZES, normalize_cluster_size, seed_ovirt_demo
from app.ovirt.seed import clear_ovirt_state, ovirt_demo_summary, seed_ovirt
from app.web.assets import console_html

router = APIRouter(tags=["Simulator"])


@router.get("/ui/static/{name}", include_in_schema=False)
async def ui_static(name: str):
    from fastapi.responses import FileResponse

    from app.web.assets import static_path
    path = static_path(name)
    if path is None:
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(path)


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
@router.get("/console", response_class=HTMLResponse, include_in_schema=True)
async def console() -> HTMLResponse:
    """Interactive API console and datacenter overview."""

    return HTMLResponse(
        console_html(),
        headers={"Cache-Control": "no-store"},
    )


@router.get("/ui/api/versions", include_in_schema=False)
async def ui_versions(request: Request) -> JSONResponse:
    from app.web.ovirt_catalog import ovirt_series_majors

    runtime_version = _runtime_version(request)
    majors = ovirt_series_majors(runtime_version)
    return JSONResponse(
        {
            "majors": majors,
            "runtime_version": runtime_version,
            "default_major": next(
                (m["major"] for m in majors if m.get("active")),
                next((m["major"] for m in majors if m["series"] == "4.5"), 45),
            ),
        }
    )


@router.get("/ui/api/catalog", include_in_schema=False)
async def ui_catalog(
    request: Request,
    major: Annotated[int, Query(ge=30, le=50)],
) -> JSONResponse:
    from app.web.ovirt_catalog import ovirt_catalog_payload

    try:
        return JSONResponse(ovirt_catalog_payload(major))
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/ui/api/method", include_in_schema=False)
async def ui_method(
    request: Request,
    major: Annotated[int, Query(ge=30, le=50)],
    path: Annotated[str, Query(min_length=1)],
    verb: Annotated[str, Query(min_length=1)],
) -> JSONResponse:
    from app.web.ovirt_catalog import ovirt_method_payload

    return JSONResponse(
        ovirt_method_payload(
            major=major,
            path=path,
            verb=verb,
            runtime_version=_runtime_version(request),
        )
    )


@router.get("/ui/api/compatibility", include_in_schema=False)
async def ui_compatibility(
    request: Request,
    major: Annotated[int, Query(ge=30, le=50)],
) -> JSONResponse:
    from app.web.ovirt_catalog import ovirt_compatibility_payload

    return JSONResponse(
        ovirt_compatibility_payload(
            major=major,
            runtime_version=_runtime_version(request),
            schema_ops_mounted=getattr(request.app.state, "ovirt_schema_ops", None),
        )
    )


@router.post("/ui/api/contract/apply", include_in_schema=False)
async def ui_contract_apply(
    request: Request,
    major: Annotated[int, Query(ge=30, le=50)],
) -> JSONResponse:
    """Hot-swap the in-memory runtime Engine series pack."""

    from app.ovirt.contract_loader import series_for_major
    from app.ovirt.schema_engine import remount_schema_services

    series = series_for_major(major)
    async with request.app.state.contract_swap_lock:
        try:
            ops = remount_schema_services(request.app, series)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse(
        {
            "ok": True,
            "major": major,
            "series": series,
            "runtime_version": f"ovirt-{series}",
            "method_count": ops,
            "operation_count": ops,
        }
    )


@router.get("/ui/api/demo/state", include_in_schema=False)
async def ui_demo_state(request: Request) -> JSONResponse:
    pool = _database_pool(request)
    async with pool.acquire() as connection:
        return JSONResponse(await ovirt_demo_summary(connection))


@router.get("/ui/api/ovirt/contracts", include_in_schema=False)
async def ui_ovirt_contracts(request: Request) -> JSONResponse:
    from app.ovirt.contract_loader import ensure_loaded, get_runtime, list_series

    ensure_loaded(getattr(request.app.state, "ovirt_series", "4.5"))
    runtime = get_runtime()
    return JSONResponse(
        {
            "active": runtime.summary(),
            "available": list_series(),
            "schema_ops_mounted": getattr(request.app.state, "ovirt_schema_ops", 0),
        }
    )


@router.post("/ui/api/ovirt/contracts/activate", include_in_schema=False)
async def ui_ovirt_contracts_activate(request: Request) -> JSONResponse:
    from app.ovirt.schema_engine import remount_schema_services

    payload = await request.json()
    series = str(payload.get("series") or "").lower().strip()
    if not series:
        raise HTTPException(status_code=400, detail="series is required")
    async with request.app.state.contract_swap_lock:
        try:
            ops = remount_schema_services(request.app, series)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse(
        {"ok": True, "runtime_version": f"ovirt-{series}", "series": series, "operation_count": ops}
    )


@router.post("/ui/api/demo/load", include_in_schema=False)
async def ui_demo_load(request: Request) -> JSONResponse:
    """Load a sized demo cluster: small (3h/50vm), large (10h/1000vm), big (30h/2000vm)."""

    size_raw = request.query_params.get("size") or request.query_params.get("profile")
    if size_raw is None:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if isinstance(body, dict):
            size_raw = body.get("size") or body.get("profile")
    try:
        size = normalize_cluster_size(str(size_raw) if size_raw else "large")
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=f"{error}; sizes: {', '.join(sorted(CLUSTER_SIZES))}",
        ) from error

    pool = _database_pool(request)
    try:
        async with pool.acquire() as connection:
            async with connection.transaction():
                result = await seed_ovirt_demo(connection, size=size)
            summary = await ovirt_demo_summary(connection)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"failed to load oVirt demo datacenter: {error}"
        ) from error
    return JSONResponse({"ok": True, "profile": result["profile"], "summary": summary, "seed": result})


@router.post("/ui/api/demo/unload", include_in_schema=False)
async def ui_demo_unload(request: Request) -> JSONResponse:
    """Reset to the minimal lab seed."""

    pool = _database_pool(request)
    try:
        async with pool.acquire() as connection:
            async with connection.transaction():
                await clear_ovirt_state(connection)
                result = await seed_ovirt(connection)
            summary = await ovirt_demo_summary(connection)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"failed to remove demo data: {error}"
        ) from error
    return JSONResponse({"ok": True, "profile": result.get("profile", "minimal"), "summary": summary})


@router.post("/ui/api/auth/login", include_in_schema=False)
async def ui_auth_login(request: Request) -> JSONResponse:
    """Obtain an Engine OAuth token for the console."""

    from app.ovirt.auth import issue_oauth_token

    payload = await request.json()
    username = str(payload.get("username") or "admin@internal")
    password = str(payload.get("password") or "")
    pool = _database_pool(request)
    async with pool.acquire() as connection:
        token = await issue_oauth_token(connection, username=username, password=password)
    return JSONResponse({"ok": True, **token, "username": username})


def _database_pool(request: Request) -> Pool:
    database = get_database(request)
    if not isinstance(database, AsyncpgDatabase):
        raise HTTPException(status_code=503, detail="database is not available")
    return database.pool


def _runtime_version(request: Request) -> str | None:
    for attr in ("runtime_source_version", "runtime_version"):
        active = getattr(request.app.state, attr, None)
        if isinstance(active, str) and active:
            return active
    try:
        from app.ovirt.contract_loader import get_runtime

        runtime = get_runtime()
        if runtime.series:
            return f"ovirt-{runtime.series}"
    except Exception:
        pass
    return None
