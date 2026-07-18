"""Specialized stateful Engine API routes (root, vms, disks, hosts, networks, storage, jobs)."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from asyncpg import Connection
from fastapi import APIRouter, Request, Response

from app.ovirt.deps import get_db, require_auth
from app.ovirt.errors import OVirtError
from app.ovirt.jobs import create_job, respond_action
from app.ovirt.repr import (
    cluster_entity,
    datacenter_entity,
    disk_attachment_entity,
    disk_entity,
    host_entity,
    job_entity,
    network_entity,
    nic_entity,
    snapshot_entity,
    storage_domain_entity,
    tag_entity,
    template_entity,
    user_entity,
    vm_entity,
)
from app.ovirt.serialize import parse_body, respond, unwrap_entity, wants_xml
from app.ovirt.settings import (
    OPT_DEFAULT_CLUSTER_CPU_TYPE,
    OPT_DEFAULT_CPU_CORES,
    OPT_DEFAULT_CPU_SOCKETS,
    OPT_DEFAULT_CPU_THREADS,
    OPT_DEFAULT_DC_STATUS,
    OPT_DEFAULT_DISK_FORMAT,
    OPT_DEFAULT_DISK_INTERFACE,
    OPT_DEFAULT_DISK_SIZE,
    OPT_DEFAULT_HOST_ADDRESS,
    OPT_DEFAULT_HOST_CPU_CORES,
    OPT_DEFAULT_HOST_MEMORY,
    OPT_DEFAULT_HOST_STATUS,
    OPT_DEFAULT_MAC_PREFIX,
    OPT_DEFAULT_NIC_INTERFACE,
    OPT_DEFAULT_NIC_NAME,
    OPT_DEFAULT_OS_TYPE,
    OPT_DEFAULT_SD_AVAILABLE,
    OPT_DEFAULT_SD_STATUS,
    OPT_DEFAULT_SD_TYPE,
    OPT_DEFAULT_SNAPSHOT_DESCRIPTION,
    OPT_DEFAULT_STORAGE_CONNECTION_TYPE,
    OPT_DEFAULT_STORAGE_TYPE,
    OPT_DEFAULT_TAG_NAME,
    OPT_DEFAULT_VM_MEMORY,
    OPT_DEFAULT_VM_STATUS,
    OPT_DEFAULT_VM_TYPE,
    OPT_HOST_ACTION_STATUS_MAP,
    OPT_SD_ATTACH_ACTIVE,
    OPT_SD_ATTACH_MAINTENANCE,
    OPT_VM_ACTION_STATUS_MAP,
    option_int,
    option_json,
    option_value,
    product_info_from_db,
)
from app.ovirt.versioning import strip_api_prefix

router = APIRouter(tags=["engine"])


def _match(path: str, pattern: str) -> re.Match[str] | None:
    return re.fullmatch(pattern, path)


async def _search_filter(rows: list[Any], search: str | None, name_attr: str = "name") -> list[Any]:
    if not search:
        return rows
    # Support name=foo and name=foo*
    m = re.search(r"name\s*=\s*([^\s]+)", search, re.I)
    if not m:
        return rows
    pattern = m.group(1).strip("=")
    case_sensitive = False
    if pattern.startswith("="):
        pattern = pattern[1:]
        case_sensitive = True
    wildcard = pattern.endswith("*")
    needle = pattern[:-1] if wildcard else pattern

    def ok(row: Any) -> bool:
        value = str(row[name_attr])
        if not case_sensitive:
            value = value.lower()
            n = needle.lower()
        else:
            n = needle
        return value.startswith(n) if wildcard else value == n

    return [r for r in rows if ok(r)]


async def api_root(request: Request, conn: Connection, series: str) -> Response:
    from app.ovirt.contract_loader import ensure_loaded, get_runtime

    ensure_loaded(series)
    rt = get_runtime()
    pack = rt.pack
    # Entry-point link catalog comes from the active contract pack (routing metadata).
    # Inventory counts + product_info come from Postgres.
    links = (pack.entry_point_links if pack else []) or []
    summary = {
        "hosts": {
            "active": await conn.fetchval("SELECT count(*) FROM ov_hosts WHERE status='up'") or 0,
            "total": await conn.fetchval("SELECT count(*) FROM ov_hosts") or 0,
        },
        "storage_domains": {
            "active": await conn.fetchval(
                "SELECT count(*) FROM ov_storage_domains WHERE status='active'"
            )
            or 0,
            "total": await conn.fetchval("SELECT count(*) FROM ov_storage_domains") or 0,
        },
        "users": {
            "active": await conn.fetchval("SELECT count(*) FROM ov_users WHERE enabled") or 0,
            "total": await conn.fetchval("SELECT count(*) FROM ov_users") or 0,
        },
        "vms": {
            "active": await conn.fetchval("SELECT count(*) FROM ov_vms WHERE status='up'") or 0,
            "total": await conn.fetchval("SELECT count(*) FROM ov_vms") or 0,
        },
    }
    blank = await conn.fetchrow("SELECT id FROM ov_templates WHERE name='Blank' LIMIT 1")
    entity: dict[str, Any] = {
        "link": [{"rel": l["rel"], "href": l["href"]} for l in links],
        "product_info": await product_info_from_db(conn),
        "summary": summary,
        "time": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    if blank:
        entity["special_objects"] = {
            "blank_template": {
                "id": str(blank["id"]),
                "href": f"/ovirt-engine/api/templates/{blank['id']}",
            }
        }
    return respond(request, element="api", data=entity)


async def handle_engine_request(request: Request) -> Response:
    """Shared Engine entrypoint used by contract-registered routes and fallbacks."""

    auth = await require_auth(request)
    db = get_db(request)
    rel = strip_api_prefix(request.url.path)
    if rel.startswith("/"):
        rel = rel[1:]
    method = request.method.upper()
    if method == "HEAD":
        method = "GET"
    raw = await request.body()
    payload = parse_body(raw, request.headers.get("content-type"))
    try:
        async with db.pool.acquire() as conn:
            return await _dispatch(request, conn, auth.user_id, method, rel, payload)
    except OVirtError:
        raise
    except (TypeError, AttributeError) as exc:
        # Missing rows often crash in *_entity builders (row is None).
        raise OVirtError("NotFound", "resource not found", status_code=404) from exc
    except Exception as exc:
        # Integrity / UUID parse failures from coverage mutations → client error.
        name = type(exc).__name__
        detail = str(exc).split("\n", 1)[0][:200]
        if name in {
            "ForeignKeyViolationError",
            "UniqueViolationError",
            "NotNullViolationError",
            "CheckViolationError",
            "DataError",
            "InvalidTextRepresentationError",
        } or "invalid input syntax for type uuid" in detail:
            raise OVirtError("BadRequest", detail or name, status_code=400) from exc
        raise


# Catch-all fallback for paths outside the active pack (hidden from OpenAPI —
# each contract operation is registered individually via app.ovirt.registry).
@router.api_route(
    "/ovirt-engine/api",
    methods=["GET", "HEAD"],
    include_in_schema=False,
    name="ovirt-fallback:api",
)
@router.api_route(
    "/ovirt-engine/api/",
    methods=["GET", "HEAD"],
    include_in_schema=False,
    name="ovirt-fallback:api-slash",
)
@router.api_route(
    "/ovirt-engine/api/v3",
    methods=["GET", "HEAD"],
    include_in_schema=False,
    name="ovirt-fallback:api-v3",
)
@router.api_route(
    "/ovirt-engine/api/v3/",
    methods=["GET", "HEAD"],
    include_in_schema=False,
    name="ovirt-fallback:api-v3-slash",
)
@router.api_route(
    "/ovirt-engine/api/v4",
    methods=["GET", "HEAD"],
    include_in_schema=False,
    name="ovirt-fallback:api-v4",
)
@router.api_route(
    "/ovirt-engine/api/v4/",
    methods=["GET", "HEAD"],
    include_in_schema=False,
    name="ovirt-fallback:api-v4-slash",
)
async def engine_root(request: Request) -> Response:
    return await handle_engine_request(request)


@router.api_route(
    "/ovirt-engine/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "HEAD"],
    include_in_schema=False,
    name="ovirt-fallback:dispatch",
)
@router.api_route(
    "/ovirt-engine/api/v3/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "HEAD"],
    include_in_schema=False,
    name="ovirt-fallback:dispatch-v3",
)
@router.api_route(
    "/ovirt-engine/api/v4/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "HEAD"],
    include_in_schema=False,
    name="ovirt-fallback:dispatch-v4",
)
async def engine_dispatch(request: Request, path: str) -> Response:
    del path
    return await handle_engine_request(request)


async def _dispatch(
    request: Request,
    conn: Connection,
    user_id: Any,
    method: str,
    path: str,
    payload: dict[str, Any],
) -> Response:
    # Engine URLs may use camelCase segments (e.g. imageTransfers); inventory keys are lowercase.
    parts = [p.lower() for p in path.split("/") if p]
    if not parts:
        series = getattr(request.app.state, "ovirt_series", "4.5")
        return await api_root(request, conn, series)

    # --- VMs ---
    if parts[0] == "vms":
        return await _handle_vms(request, conn, user_id, method, parts, payload)

    # --- Disks ---
    if parts[0] == "disks":
        return await _handle_disks(request, conn, user_id, method, parts, payload)

    # --- Hosts ---
    if parts[0] == "hosts":
        return await _handle_hosts(request, conn, user_id, method, parts, payload)

    # --- Datacenters ---
    if parts[0] == "datacenters":
        return await _handle_datacenters(request, conn, method, parts, payload)

    # --- Clusters ---
    if parts[0] == "clusters":
        return await _handle_clusters(request, conn, method, parts, payload)

    # --- Networks / vnicprofiles ---
    if parts[0] == "networks":
        return await _handle_networks(request, conn, method, parts, payload)
    if parts[0] == "vnicprofiles":
        return await _handle_vnicprofiles(request, conn, method, parts, payload)

    # --- Storage ---
    if parts[0] == "storagedomains":
        return await _handle_storage_domains(request, conn, method, parts, payload)
    if parts[0] == "storageconnections":
        return await _handle_storage_connections(request, conn, method, parts, payload)

    # --- Templates ---
    if parts[0] == "templates":
        return await _handle_templates(request, conn, method, parts, payload)

    # --- Identity ---
    if parts[0] == "users":
        return await _handle_users(request, conn, method, parts, payload)
    if parts[0] == "roles":
        return await _handle_simple_table(
            request,
            conn,
            method,
            parts,
            "ov_roles",
            "roles",
            "role",
            ["name", "description"],
            payload,
        )
    if parts[0] == "groups":
        return await _handle_groups(request, conn, method, parts, payload)
    if parts[0] == "domains":
        return await _handle_domains(request, conn, method, parts)
    if parts[0] == "permissions":
        return await _handle_permissions(request, conn, method, parts)

    # --- Jobs / events / tags / bookmarks ---
    if parts[0] == "jobs":
        return await _handle_jobs(request, conn, method, parts, payload)
    if parts[0] == "events":
        return await _handle_events(request, conn, method, parts)
    if parts[0] == "tags":
        return await _handle_simple_table(
            request,
            conn,
            method,
            parts,
            "ov_tags",
            "tags",
            "tag",
            ["name", "description"],
            payload,
        )
    if parts[0] == "bookmarks":
        return await _handle_simple_table(
            request,
            conn,
            method,
            parts,
            "ov_bookmarks",
            "bookmarks",
            "bookmark",
            ["name", "value"],
            payload,
        )

    # Fall through to schema/generic object store
    from app.ovirt.schema_engine import handle_generic

    return await handle_generic(request, conn, method, parts, payload)


async def _handle_vms(
    request: Request,
    conn: Connection,
    user_id: Any,
    method: str,
    parts: list[str],
    payload: dict[str, Any],
) -> Response:
    search = request.query_params.get("search")
    max_results = request.query_params.get("max")
    if len(parts) == 1:
        if method == "GET":
            rows = await conn.fetch("SELECT * FROM ov_vms ORDER BY name")
            rows = await _search_filter(rows, search)
            if max_results:
                rows = rows[: int(max_results)]
            return respond(
                request, element="vm", collection="vms", data=[vm_entity(r) for r in rows]
            )
        if method == "POST":
            body = unwrap_entity(payload, "vm")
            name = str(body.get("name") or f"vm-{uuid4().hex[:8]}")
            cluster = body.get("cluster") or {}
            cluster_id = cluster.get("id") if isinstance(cluster, dict) else None
            if not cluster_id:
                cluster_id = await conn.fetchval("SELECT id FROM ov_clusters ORDER BY name LIMIT 1")
            if not cluster_id:
                raise OVirtError("BadRequest", "cluster is required", status_code=400)
            template = body.get("template") or {}
            template_id = template.get("id") if isinstance(template, dict) else None
            if not template_id:
                template_id = await conn.fetchval(
                    "SELECT id FROM ov_templates WHERE name='Blank' LIMIT 1"
                )
            memory = int(body.get("memory") or await option_int(conn, OPT_DEFAULT_VM_MEMORY))
            cpu = body.get("cpu") or {}
            topology = cpu.get("topology") if isinstance(cpu, dict) else {}
            sockets = int(
                (topology or {}).get("sockets") or await option_int(conn, OPT_DEFAULT_CPU_SOCKETS)
            )
            cores = int(
                (topology or {}).get("cores") or await option_int(conn, OPT_DEFAULT_CPU_CORES)
            )
            threads = int(
                (topology or {}).get("threads") or await option_int(conn, OPT_DEFAULT_CPU_THREADS)
            )
            os_type = await option_value(conn, OPT_DEFAULT_OS_TYPE)
            if isinstance(body.get("os"), dict):
                os_type = str(body["os"].get("type") or os_type)
            vm_status = await option_value(conn, OPT_DEFAULT_VM_STATUS)
            vid = uuid4()
            await conn.execute(
                """INSERT INTO ov_vms(id, cluster_id, template_id, name, description, status,
                   memory, cpu_sockets, cpu_cores, cpu_threads, os_type, type, data)
                   VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb)""",
                vid,
                cluster_id,
                template_id,
                name,
                str(body.get("description") or ""),
                vm_status,
                memory,
                sockets,
                cores,
                threads,
                os_type,
                str(body.get("type") or await option_value(conn, OPT_DEFAULT_VM_TYPE)),
                json.dumps({}),
            )
            # optional disk from body
            row = await conn.fetchrow("SELECT * FROM ov_vms WHERE id=$1", vid)
            await create_job(conn, description=f"Add VM {name}", owner_id=user_id)
            return respond(request, element="vm", data=vm_entity(row), status_code=201)

    vm_id = parts[1]
    row = await conn.fetchrow("SELECT * FROM ov_vms WHERE id=$1::uuid", vm_id)
    if row is None and method != "POST":
        # allow action create paths to 404 consistently
        pass

    if len(parts) == 2:
        if method == "GET":
            if row is None:
                raise OVirtError("NotFound", f"VM {vm_id} not found", status_code=404)
            return respond(request, element="vm", data=vm_entity(row))
        if method == "PUT":
            if row is None:
                raise OVirtError("NotFound", f"VM {vm_id} not found", status_code=404)
            body = unwrap_entity(payload, "vm")
            name = str(body.get("name") or row["name"])
            description = str(body.get("description") if "description" in body else row["description"])
            memory = int(body.get("memory") or row["memory"])
            cpu = body.get("cpu") or {}
            topology = cpu.get("topology") if isinstance(cpu, dict) else None
            sockets = int((topology or {}).get("sockets") or row["cpu_sockets"])
            cores = int((topology or {}).get("cores") or row["cpu_cores"])
            threads = int((topology or {}).get("threads") or row["cpu_threads"])
            await conn.execute(
                """UPDATE ov_vms SET name=$2, description=$3, memory=$4,
                   cpu_sockets=$5, cpu_cores=$6, cpu_threads=$7, updated_at=now()
                   WHERE id=$1::uuid""",
                vm_id,
                name,
                description,
                memory,
                sockets,
                cores,
                threads,
            )
            row = await conn.fetchrow("SELECT * FROM ov_vms WHERE id=$1::uuid", vm_id)
            return respond(request, element="vm", data=vm_entity(row))
        if method == "DELETE":
            if row is None:
                raise OVirtError("NotFound", f"VM {vm_id} not found", status_code=404)
            await conn.execute("DELETE FROM ov_vms WHERE id=$1::uuid", vm_id)
            await create_job(conn, description=f"Remove VM {row['name']}", owner_id=user_id)
            return Response(status_code=200 if wants_xml(request) else 200)

    # Subcollections first (must win over action names for POST …/vms/{id}/snapshots etc.)
    if len(parts) >= 3:
        sub = parts[2]
        if sub == "diskattachments":
            return await _vm_disk_attachments(request, conn, method, parts, payload)
        if sub == "nics":
            return await _vm_nics(request, conn, method, parts, payload)
        if sub == "snapshots":
            return await _vm_snapshots(request, conn, user_id, method, parts, payload)
        if sub == "tags":
            return await _vm_tags(request, conn, method, parts, payload)
        if sub in {
            "cdroms",
            "permissions",
            "graphicsconsoles",
            "reporteddevices",
            "sessions",
            "applications",
            "watchdogs",
            "hostdevices",
            "katelloerrata",
            "numanodes",
            "mediateddevices",
            "affinitylabels",
            "statistics",
        }:
            from app.ovirt.schema_engine import handle_subcollection

            return await handle_subcollection(
                request, conn, method, "vms", vm_id, sub, parts[3:], payload
            )

    if len(parts) == 3 and method == "POST":
        action = parts[2]
        if row is None:
            raise OVirtError("NotFound", f"VM {vm_id} not found", status_code=404)
        if action == "clone":
            body = unwrap_entity(payload, "vm") if payload else {}
            new_name = str(body.get("name") or f"{row['name']}-clone")
            new_id = uuid4()
            await conn.execute(
                """INSERT INTO ov_vms(id, cluster_id, template_id, name, description, status,
                   memory, cpu_sockets, cpu_cores, cpu_threads, os_type, type, data)
                   VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,'{}'::jsonb)""",
                new_id,
                row["cluster_id"],
                row["template_id"],
                new_name,
                row["description"],
                await option_value(conn, OPT_DEFAULT_VM_STATUS),
                row["memory"],
                row["cpu_sockets"],
                row["cpu_cores"],
                row["cpu_threads"],
                row["os_type"],
                row["type"],
            )
            return await respond_action(
                request, conn, description=f"Clone VM {row['name']}", owner_id=user_id
            )
        if action in {
            "preview_snapshot",
            "commit_snapshot",
            "undo_snapshot",
            "export",
            "detach",
            "ticket",
            "screenthumbnail",
        }:
            return await respond_action(
                request, conn, description=f"VM {action}", owner_id=user_id
            )
        vm_actions = await option_json(conn, OPT_VM_ACTION_STATUS_MAP)
        if action in vm_actions:
            new_status = str(vm_actions[action])
            host_id = row["host_id"]
            if action == "start" and host_id is None:
                host_id = await conn.fetchval(
                    "SELECT id FROM ov_hosts WHERE cluster_id=$1 AND status='up' LIMIT 1",
                    row["cluster_id"],
                )
            if action in {"stop", "shutdown", "suspend"}:
                host_id = None if action != "suspend" else host_id
            await conn.execute(
                "UPDATE ov_vms SET status=$2, host_id=$3, updated_at=now() WHERE id=$1::uuid",
                vm_id,
                new_status,
                host_id,
            )
            return await respond_action(
                request, conn, description=f"VM {action} {row['name']}", owner_id=user_id
            )
        raise OVirtError("BadRequest", f"Unknown action {action}", status_code=400)

    raise OVirtError("NotFound", f"No handler for /vms/{'/'.join(parts[1:])}", status_code=404)


async def _fetch_disk_attachment(conn: Connection, aid: str, vm_id: str) -> Any:
    return await conn.fetchrow(
        """SELECT a.*, d.name AS disk_name
           FROM ov_disk_attachments a JOIN ov_disks d ON d.id=a.disk_id
           WHERE a.id=$1::uuid AND a.vm_id=$2::uuid""",
        aid,
        vm_id,
    )


async def _vm_disk_attachments(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    vm_id = parts[1]
    if len(parts) == 3:
        if method == "GET":
            rows = await conn.fetch(
                """SELECT a.*, d.name AS disk_name, d.provisioned_size, d.format
                   FROM ov_disk_attachments a JOIN ov_disks d ON d.id=a.disk_id
                   WHERE a.vm_id=$1::uuid""",
                vm_id,
            )
            items = [disk_attachment_entity(r, vm_id=vm_id) for r in rows]
            return respond(
                request, element="disk_attachment", collection="disk_attachments", data=items
            )
        if method == "POST":
            body = unwrap_entity(payload, "disk_attachment")
            disk = body.get("disk") or {}
            disk_id = disk.get("id") if isinstance(disk, dict) else None
            if not disk_id:
                size = int(
                    (disk or {}).get("provisioned_size")
                    or await option_int(conn, OPT_DEFAULT_DISK_SIZE)
                )
                disk_id = uuid4()
                sd = await conn.fetchval("SELECT id FROM ov_storage_domains ORDER BY name LIMIT 1")
                await conn.execute(
                    """INSERT INTO ov_disks(id, name, provisioned_size, actual_size, storage_domain_id)
                       VALUES($1,$2,$3,$3,$4)""",
                    disk_id,
                    str((disk or {}).get("name") or f"disk-{disk_id.hex[:8]}"),
                    size,
                    sd,
                )
            aid = uuid4()
            await conn.execute(
                """INSERT INTO ov_disk_attachments(id, vm_id, disk_id, active, bootable, interface)
                   VALUES($1,$2::uuid,$3::uuid,$4,$5,$6)""",
                aid,
                vm_id,
                disk_id,
                bool(body.get("active", True)),
                bool(body.get("bootable", False)),
                str(
                    body.get("interface")
                    or await option_value(conn, OPT_DEFAULT_DISK_INTERFACE)
                ),
            )
            row = await _fetch_disk_attachment(conn, str(aid), vm_id)
            return respond(
                request,
                element="disk_attachment",
                data=disk_attachment_entity(row, vm_id=vm_id),
                status_code=201,
            )
    if len(parts) == 4:
        aid = parts[3]
        if method == "GET":
            r = await _fetch_disk_attachment(conn, aid, vm_id)
            if r is None:
                raise OVirtError("NotFound", "disk attachment not found", status_code=404)
            return respond(
                request,
                element="disk_attachment",
                data=disk_attachment_entity(r, vm_id=vm_id),
            )
        if method == "DELETE":
            await conn.execute(
                "DELETE FROM ov_disk_attachments WHERE id=$1::uuid AND vm_id=$2::uuid", aid, vm_id
            )
            return Response(status_code=200)
    raise OVirtError("NotFound", "diskattachments path", status_code=404)


async def _vm_nics(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    vm_id = parts[1]
    if len(parts) == 3 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_nics WHERE vm_id=$1::uuid ORDER BY name", vm_id)
        items = [nic_entity(r, vm_id=vm_id) for r in rows]
        return respond(request, element="nic", collection="nics", data=items)
    if len(parts) == 3 and method == "POST":
        body = unwrap_entity(payload, "nic")
        nid = uuid4()
        profile = body.get("vnic_profile") or {}
        profile_id = profile.get("id") if isinstance(profile, dict) else None
        if not profile_id:
            profile_id = await conn.fetchval("SELECT id FROM ov_vnic_profiles LIMIT 1")
        mac_prefix = await option_value(conn, OPT_DEFAULT_MAC_PREFIX)
        mac = mac_prefix + ":" + ":".join(f"{(nid.int >> (8 * i)) & 0xFF:02x}" for i in range(3))
        await conn.execute(
            """INSERT INTO ov_nics(id, vm_id, name, interface, mac_address, vnic_profile_id)
               VALUES($1,$2::uuid,$3,$4,$5,$6)""",
            nid,
            vm_id,
            str(body.get("name") or await option_value(conn, OPT_DEFAULT_NIC_NAME)),
            str(body.get("interface") or await option_value(conn, OPT_DEFAULT_NIC_INTERFACE)),
            mac,
            profile_id,
        )
        row = await conn.fetchrow(
            "SELECT * FROM ov_nics WHERE id=$1 AND vm_id=$2::uuid", nid, vm_id
        )
        return respond(
            request, element="nic", data=nic_entity(row, vm_id=vm_id), status_code=201
        )
    if len(parts) >= 4:
        nic_id = parts[3]
        if len(parts) == 4 and method == "DELETE":
            await conn.execute(
                "DELETE FROM ov_nics WHERE id=$1::uuid AND vm_id=$2::uuid", nic_id, vm_id
            )
            return Response(status_code=200)
        if len(parts) == 4 and method == "PUT":
            body = unwrap_entity(payload, "nic")
            profile = body.get("vnic_profile") or {}
            profile_id = profile.get("id") if isinstance(profile, dict) else None
            if profile_id:
                await conn.execute(
                    "UPDATE ov_nics SET vnic_profile_id=$3::uuid, name=COALESCE($4,name) WHERE id=$1::uuid AND vm_id=$2::uuid",
                    nic_id,
                    vm_id,
                    profile_id,
                    body.get("name"),
                )
            r = await conn.fetchrow(
                "SELECT * FROM ov_nics WHERE id=$1::uuid AND vm_id=$2::uuid", nic_id, vm_id
            )
            return respond(request, element="nic", data=nic_entity(r, vm_id=vm_id))
        if len(parts) == 5 and method == "POST" and parts[4] in {"activate", "deactivate"}:
            plugged = parts[4] == "activate"
            await conn.execute(
                "UPDATE ov_nics SET plugged=$3 WHERE id=$1::uuid AND vm_id=$2::uuid",
                nic_id,
                vm_id,
                plugged,
            )
            return await respond_action(
                request, conn, description=f"NIC {parts[4]}", owner_id=None
            )
    raise OVirtError("NotFound", "nics path", status_code=404)


async def _vm_snapshots(
    request: Request,
    conn: Connection,
    user_id: Any,
    method: str,
    parts: list[str],
    payload: dict[str, Any],
) -> Response:
    vm_id = parts[1]
    if len(parts) == 3 and method == "GET":
        rows = await conn.fetch(
            "SELECT * FROM ov_snapshots WHERE vm_id=$1::uuid ORDER BY created_at", vm_id
        )
        items = [snapshot_entity(r, vm_id=vm_id) for r in rows]
        return respond(request, element="snapshot", collection="snapshots", data=items)
    if len(parts) == 3 and method == "POST":
        body = unwrap_entity(payload, "snapshot")
        sid = uuid4()
        await conn.execute(
            """INSERT INTO ov_snapshots(id, vm_id, description, persist_memorystate)
               VALUES($1,$2::uuid,$3,$4)""",
            sid,
            vm_id,
            str(body.get("description") or await option_value(conn, OPT_DEFAULT_SNAPSHOT_DESCRIPTION)),
            bool(body.get("persist_memorystate", False)),
        )
        await create_job(conn, description="Create snapshot", owner_id=user_id)
        row = await conn.fetchrow(
            "SELECT * FROM ov_snapshots WHERE id=$1 AND vm_id=$2::uuid", sid, vm_id
        )
        return respond(
            request, element="snapshot", data=snapshot_entity(row, vm_id=vm_id), status_code=201
        )
    if len(parts) == 4 and method == "DELETE":
        await conn.execute(
            "DELETE FROM ov_snapshots WHERE id=$1::uuid AND vm_id=$2::uuid", parts[3], vm_id
        )
        return Response(status_code=200)
    if len(parts) == 5 and method == "POST" and parts[4] == "restore":
        return await respond_action(
            request, conn, description="Restore snapshot", owner_id=user_id
        )
    raise OVirtError("NotFound", "snapshots path", status_code=404)


async def _vm_tags(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    vm_id = parts[1]
    if len(parts) == 3 and method == "GET":
        rows = await conn.fetch(
            """SELECT t.* FROM ov_tags t
               JOIN ov_tag_assignments a ON a.tag_id=t.id
               WHERE a.object_type='vm' AND a.object_id=$1::uuid""",
            vm_id,
        )
        items = [tag_entity(r) for r in rows]
        return respond(request, element="tag", collection="tags", data=items)
    if len(parts) == 3 and method == "POST":
        body = unwrap_entity(payload, "tag")
        tag_id = body.get("id")
        if not tag_id:
            tag_id = uuid4()
            await conn.execute(
                "INSERT INTO ov_tags(id, name) VALUES($1,$2) ON CONFLICT (name) DO NOTHING",
                tag_id,
                str(body.get("name") or await option_value(conn, OPT_DEFAULT_TAG_NAME)),
            )
            existing = await conn.fetchval("SELECT id FROM ov_tags WHERE name=$1", body.get("name"))
            tag_id = existing or tag_id
        await conn.execute(
            """INSERT INTO ov_tag_assignments(id, tag_id, object_type, object_id)
               VALUES($1,$2::uuid,'vm',$3::uuid) ON CONFLICT DO NOTHING""",
            uuid4(),
            tag_id,
            vm_id,
        )
        row = await conn.fetchrow("SELECT * FROM ov_tags WHERE id=$1::uuid", tag_id)
        return respond(request, element="tag", data=tag_entity(row), status_code=201)
    raise OVirtError("NotFound", "tags path", status_code=404)


# ---- Disks / Hosts / DC / Clusters / Networks / Storage / Templates / Users / Jobs ----

async def _handle_disks(
    request: Request, conn: Connection, user_id: Any, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    search = request.query_params.get("search")
    if len(parts) == 1:
        if method == "GET":
            rows = await conn.fetch("SELECT * FROM ov_disks ORDER BY name")
            rows = await _search_filter(rows, search)
            return respond(
                request, element="disk", collection="disks", data=[disk_entity(r) for r in rows]
            )
        if method == "POST":
            body = unwrap_entity(payload, "disk")
            did = uuid4()
            size = int(body.get("provisioned_size") or await option_int(conn, OPT_DEFAULT_DISK_SIZE))
            sd = body.get("storage_domains", {}).get("storage_domain")
            sd_id = None
            if isinstance(sd, list) and sd:
                sd_id = sd[0].get("id")
            elif isinstance(sd, dict):
                sd_id = sd.get("id")
            if not sd_id:
                sd_id = await conn.fetchval("SELECT id FROM ov_storage_domains LIMIT 1")
            await conn.execute(
                """INSERT INTO ov_disks(id, name, description, provisioned_size, actual_size,
                   format, sparse, storage_domain_id)
                   VALUES($1,$2,$3,$4,$4,$5,$6,$7)""",
                did,
                str(body.get("name") or f"disk-{did.hex[:8]}"),
                str(body.get("description") or ""),
                size,
                str(body.get("format") or await option_value(conn, OPT_DEFAULT_DISK_FORMAT)),
                bool(body.get("sparse", True)),
                sd_id,
            )
            row = await conn.fetchrow("SELECT * FROM ov_disks WHERE id=$1", did)
            await create_job(conn, description="Add disk", owner_id=user_id)
            return respond(request, element="disk", data=disk_entity(row), status_code=201)
    disk_id = parts[1]
    row = await conn.fetchrow("SELECT * FROM ov_disks WHERE id=$1::uuid", disk_id)
    if len(parts) == 2:
        if method == "GET":
            if row is None:
                raise OVirtError("NotFound", "disk not found", status_code=404)
            return respond(request, element="disk", data=disk_entity(row))
        if method == "PUT":
            if row is None:
                raise OVirtError("NotFound", "disk not found", status_code=404)
            body = unwrap_entity(payload, "disk")
            size = int(body.get("provisioned_size") or row["provisioned_size"])
            await conn.execute(
                """UPDATE ov_disks SET name=COALESCE($2,name), description=COALESCE($3,description),
                   provisioned_size=$4, updated_at=now() WHERE id=$1::uuid""",
                disk_id,
                body.get("name"),
                body.get("description"),
                size,
            )
            row = await conn.fetchrow("SELECT * FROM ov_disks WHERE id=$1::uuid", disk_id)
            return respond(request, element="disk", data=disk_entity(row))
        if method == "DELETE":
            await conn.execute("DELETE FROM ov_disks WHERE id=$1::uuid", disk_id)
            return Response(status_code=200)
    if len(parts) == 3 and method == "POST":
        action = parts[2]
        if action in {"copy", "export", "move", "sparsify", "reduce"}:
            body = unwrap_entity(payload, "disk") if payload else {}
            if action == "reduce" or "provisioned_size" in body or action == "move":
                # expand/reduce size when provided
                if "provisioned_size" in body:
                    await conn.execute(
                        "UPDATE ov_disks SET provisioned_size=$2, updated_at=now() WHERE id=$1::uuid",
                        disk_id,
                        int(body["provisioned_size"]),
                    )
            return await respond_action(
                request, conn, description=f"Disk {action}", owner_id=user_id
            )
    from app.ovirt.schema_engine import handle_subcollection

    if len(parts) >= 3:
        return await handle_subcollection(
            request, conn, method, "disks", disk_id, parts[2], parts[3:], payload
        )
    raise OVirtError("NotFound", "disks path", status_code=404)


async def _handle_hosts(
    request: Request, conn: Connection, user_id: Any, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    search = request.query_params.get("search")
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_hosts ORDER BY name")
        rows = await _search_filter(rows, search)
        return respond(
            request, element="host", collection="hosts", data=[host_entity(r) for r in rows]
        )
    if len(parts) == 1 and method == "POST":
        body = unwrap_entity(payload, "host")
        hid = uuid4()
        cluster = body.get("cluster") or {}
        cluster_id = cluster.get("id") if isinstance(cluster, dict) else None
        if not cluster_id:
            cluster_id = await conn.fetchval("SELECT id FROM ov_clusters LIMIT 1")
        await conn.execute(
            """INSERT INTO ov_hosts(id, cluster_id, name, address, status, memory, cpu_cores)
               VALUES($1,$2,$3,$4,$5,$6,$7)""",
            hid,
            cluster_id,
            str(body.get("name") or f"host-{hid.hex[:6]}"),
            str(body.get("address") or await option_value(conn, OPT_DEFAULT_HOST_ADDRESS)),
            await option_value(conn, OPT_DEFAULT_HOST_STATUS),
            int(body.get("memory") or await option_int(conn, OPT_DEFAULT_HOST_MEMORY)),
            int(
                (body.get("cpu") or {}).get("topology", {}).get("cores")
                or await option_int(conn, OPT_DEFAULT_HOST_CPU_CORES)
            ),
        )
        row = await conn.fetchrow("SELECT * FROM ov_hosts WHERE id=$1", hid)
        return respond(request, element="host", data=host_entity(row), status_code=201)
    host_id = parts[1]
    row = await conn.fetchrow("SELECT * FROM ov_hosts WHERE id=$1::uuid", host_id)
    if len(parts) == 2:
        if method == "GET":
            if row is None:
                raise OVirtError("NotFound", "host not found", status_code=404)
            return respond(request, element="host", data=host_entity(row))
        if method == "PUT":
            body = unwrap_entity(payload, "host")
            await conn.execute(
                "UPDATE ov_hosts SET name=COALESCE($2,name), address=COALESCE($3,address), updated_at=now() WHERE id=$1::uuid",
                host_id,
                body.get("name"),
                body.get("address"),
            )
            row = await conn.fetchrow("SELECT * FROM ov_hosts WHERE id=$1::uuid", host_id)
            return respond(request, element="host", data=host_entity(row))
        if method == "DELETE":
            await conn.execute("DELETE FROM ov_hosts WHERE id=$1::uuid", host_id)
            return Response(status_code=200)
    if len(parts) == 3 and method == "POST":
        action = parts[2].lower()
        status_map = await option_json(conn, OPT_HOST_ACTION_STATUS_MAP)
        if action in status_map:
            await conn.execute(
                "UPDATE ov_hosts SET status=$2, updated_at=now() WHERE id=$1::uuid",
                host_id,
                str(status_map[action]),
            )
            return await respond_action(
                request, conn, description=f"Host {action}", owner_id=user_id
            )
    if len(parts) >= 3 and parts[2] == "vms":
        if method == "GET" and len(parts) == 3:
            rows = await conn.fetch(
                "SELECT * FROM ov_vms WHERE host_id=$1::uuid ORDER BY name", host_id
            )
            return respond(
                request, element="vm", collection="vms", data=[vm_entity(r) for r in rows]
            )
        if method == "GET" and len(parts) == 4:
            row = await conn.fetchrow(
                "SELECT * FROM ov_vms WHERE id=$1::uuid AND host_id=$2::uuid",
                parts[3],
                host_id,
            )
            if row is None:
                raise OVirtError("NotFound", "vm not found on host", status_code=404)
            return respond(request, element="vm", data=vm_entity(row))
    from app.ovirt.schema_engine import handle_subcollection

    if len(parts) >= 3:
        return await handle_subcollection(
            request, conn, method, "hosts", host_id, parts[2], parts[3:], payload
        )
    raise OVirtError("NotFound", "hosts path", status_code=404)


async def _handle_datacenters(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_datacenters ORDER BY name")
        return respond(
            request,
            element="data_center",
            collection="data_centers",
            data=[datacenter_entity(r) for r in rows],
        )
    if len(parts) == 1 and method == "POST":
        body = unwrap_entity(payload, "data_center")
        did = uuid4()
        await conn.execute(
            """INSERT INTO ov_datacenters(id, name, description, local, status)
               VALUES($1,$2,$3,$4,$5)""",
            did,
            str(body.get("name") or f"dc-{did.hex[:6]}"),
            str(body.get("description") or ""),
            bool(body.get("local", False)),
            await option_value(conn, OPT_DEFAULT_DC_STATUS),
        )
        row = await conn.fetchrow("SELECT * FROM ov_datacenters WHERE id=$1", did)
        return respond(request, element="data_center", data=datacenter_entity(row), status_code=201)
    dc_id = parts[1]
    if len(parts) == 2 and method == "GET":
        row = await conn.fetchrow("SELECT * FROM ov_datacenters WHERE id=$1::uuid", dc_id)
        if row is None:
            raise OVirtError("NotFound", "datacenter not found", status_code=404)
        return respond(request, element="data_center", data=datacenter_entity(row))
    if len(parts) == 2 and method == "PUT":
        body = unwrap_entity(payload, "data_center")
        await conn.execute(
            "UPDATE ov_datacenters SET name=COALESCE($2,name), description=COALESCE($3,description), updated_at=now() WHERE id=$1::uuid",
            dc_id,
            body.get("name"),
            body.get("description"),
        )
        row = await conn.fetchrow("SELECT * FROM ov_datacenters WHERE id=$1::uuid", dc_id)
        return respond(request, element="data_center", data=datacenter_entity(row))
    if len(parts) == 2 and method == "DELETE":
        await conn.execute("DELETE FROM ov_datacenters WHERE id=$1::uuid", dc_id)
        return Response(status_code=200)
    if len(parts) == 3 and method == "POST" and parts[2] == "cleanfinishedtasks":
        return await respond_action(request, conn, description="Clean finished tasks")
    if len(parts) >= 3 and parts[2] == "storagedomains":
        return await _dc_storage(request, conn, method, parts, payload)
    if len(parts) >= 3 and parts[2] == "clusters":
        return await _dc_clusters(request, conn, method, parts, payload)
    if len(parts) >= 3 and parts[2] == "networks":
        return await _dc_networks(request, conn, method, parts, payload)
    if len(parts) >= 3 and parts[2] == "quotas":
        if method == "GET" and len(parts) == 3:
            rows = await conn.fetch(
                "SELECT * FROM ov_quotas WHERE datacenter_id=$1::uuid ORDER BY name", dc_id
            )
            items = [
                {
                    "id": str(r["id"]),
                    "href": f"/ovirt-engine/api/datacenters/{dc_id}/quotas/{r['id']}",
                    "name": r["name"],
                    "description": r["description"],
                }
                for r in rows
            ]
            return respond(request, element="quota", collection="quotas", data=items)
        if method == "GET" and len(parts) == 4:
            r = await conn.fetchrow(
                "SELECT * FROM ov_quotas WHERE id=$1::uuid AND datacenter_id=$2::uuid",
                parts[3],
                dc_id,
            )
            if r is None:
                raise OVirtError("NotFound", "quota not found", status_code=404)
            return respond(
                request,
                element="quota",
                data={
                    "id": str(r["id"]),
                    "href": f"/ovirt-engine/api/datacenters/{dc_id}/quotas/{r['id']}",
                    "name": r["name"],
                    "description": r["description"],
                },
            )
    from app.ovirt.schema_engine import handle_subcollection

    if len(parts) >= 3:
        return await handle_subcollection(
            request, conn, method, "datacenters", dc_id, parts[2], parts[3:], payload
        )
    raise OVirtError("NotFound", "datacenters path", status_code=404)


async def _dc_clusters(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    dc_id = parts[1]
    dc = await conn.fetchrow("SELECT id FROM ov_datacenters WHERE id=$1::uuid", dc_id)
    if dc is None:
        raise OVirtError("NotFound", "datacenter not found", status_code=404)
    if len(parts) == 3 and method == "GET":
        rows = await conn.fetch(
            "SELECT * FROM ov_clusters WHERE datacenter_id=$1::uuid ORDER BY name", dc_id
        )
        return respond(
            request,
            element="cluster",
            collection="clusters",
            data=[cluster_entity(r) for r in rows],
        )
    if len(parts) == 3 and method == "POST":
        body = unwrap_entity(payload, "cluster")
        cid = uuid4()
        await conn.execute(
            """INSERT INTO ov_clusters(id, datacenter_id, name, description, cpu_type)
               VALUES($1,$2,$3,$4,$5)""",
            cid,
            dc_id,
            str(body.get("name") or f"cluster-{cid.hex[:6]}"),
            str(body.get("description") or ""),
            str(
                (body.get("cpu") or {}).get("type")
                or body.get("cpu_type")
                or await option_value(conn, OPT_DEFAULT_CLUSTER_CPU_TYPE)
            ),
        )
        row = await conn.fetchrow("SELECT * FROM ov_clusters WHERE id=$1", cid)
        return respond(request, element="cluster", data=cluster_entity(row), status_code=201)
    if len(parts) == 4 and method == "GET":
        row = await conn.fetchrow(
            "SELECT * FROM ov_clusters WHERE id=$1::uuid AND datacenter_id=$2::uuid",
            parts[3],
            dc_id,
        )
        if row is None:
            raise OVirtError("NotFound", "cluster not found", status_code=404)
        return respond(request, element="cluster", data=cluster_entity(row))
    if len(parts) == 4 and method == "DELETE":
        await conn.execute(
            "DELETE FROM ov_clusters WHERE id=$1::uuid AND datacenter_id=$2::uuid",
            parts[3],
            dc_id,
        )
        return Response(status_code=200)
    raise OVirtError("NotFound", "datacenter clusters path", status_code=404)


async def _dc_networks(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    dc_id = parts[1]
    dc = await conn.fetchrow("SELECT id FROM ov_datacenters WHERE id=$1::uuid", dc_id)
    if dc is None:
        raise OVirtError("NotFound", "datacenter not found", status_code=404)
    if len(parts) == 3 and method == "GET":
        rows = await conn.fetch(
            "SELECT * FROM ov_networks WHERE datacenter_id=$1::uuid ORDER BY name", dc_id
        )
        return respond(
            request,
            element="network",
            collection="networks",
            data=[network_entity(r) for r in rows],
        )
    if len(parts) == 3 and method == "POST":
        body = unwrap_entity(payload, "network")
        nid = uuid4()
        vlan = body.get("vlan") or {}
        vlan_id = vlan.get("id") if isinstance(vlan, dict) else body.get("vlan_id")
        await conn.execute(
            """INSERT INTO ov_networks(id, datacenter_id, name, description, vlan_id, stp)
               VALUES($1,$2,$3,$4,$5,$6)""",
            nid,
            dc_id,
            str(body.get("name") or f"net-{nid.hex[:6]}"),
            str(body.get("description") or ""),
            int(vlan_id) if vlan_id is not None else None,
            bool(body.get("stp", False)),
        )
        row = await conn.fetchrow("SELECT * FROM ov_networks WHERE id=$1", nid)
        return respond(request, element="network", data=network_entity(row), status_code=201)
    if len(parts) == 4 and method == "GET":
        row = await conn.fetchrow(
            "SELECT * FROM ov_networks WHERE id=$1::uuid AND datacenter_id=$2::uuid",
            parts[3],
            dc_id,
        )
        if row is None:
            raise OVirtError("NotFound", "network not found", status_code=404)
        return respond(request, element="network", data=network_entity(row))
    if len(parts) == 4 and method == "DELETE":
        await conn.execute(
            "DELETE FROM ov_networks WHERE id=$1::uuid AND datacenter_id=$2::uuid",
            parts[3],
            dc_id,
        )
        return Response(status_code=200)
    raise OVirtError("NotFound", "datacenter networks path", status_code=404)


async def _dc_storage(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    dc_id = parts[1]
    if len(parts) == 3 and method == "GET":
        rows = await conn.fetch(
            """SELECT s.*, a.status AS attach_status, a.id AS attachment_id
               FROM ov_storage_domain_attachments a
               JOIN ov_storage_domains s ON s.id=a.storage_domain_id
               WHERE a.datacenter_id=$1::uuid""",
            dc_id,
        )
        items = [storage_domain_entity(r) for r in rows]
        return respond(
            request, element="storage_domain", collection="storage_domains", data=items
        )
    if len(parts) == 3 and method == "POST":
        body = unwrap_entity(payload, "storage_domain")
        sd_id = body.get("id")
        if not sd_id:
            raise OVirtError("BadRequest", "storage domain id required", status_code=400)
        await conn.execute(
            """INSERT INTO ov_storage_domain_attachments(id, storage_domain_id, datacenter_id, status)
               VALUES($1,$2::uuid,$3::uuid,$4) ON CONFLICT DO NOTHING""",
            uuid4(),
            sd_id,
            dc_id,
            await option_value(conn, OPT_SD_ATTACH_ACTIVE),
        )
        row = await conn.fetchrow("SELECT * FROM ov_storage_domains WHERE id=$1::uuid", sd_id)
        return respond(request, element="storage_domain", data=storage_domain_entity(row), status_code=201)
    if len(parts) == 5 and method == "POST" and parts[4] in {"activate", "deactivate"}:
        status = (
            await option_value(conn, OPT_SD_ATTACH_ACTIVE)
            if parts[4] == "activate"
            else await option_value(conn, OPT_SD_ATTACH_MAINTENANCE)
        )
        await conn.execute(
            """UPDATE ov_storage_domain_attachments SET status=$3
               WHERE storage_domain_id=$1::uuid AND datacenter_id=$2::uuid""",
            parts[3],
            dc_id,
            status,
        )
        return await respond_action(request, conn, description=f"Storage domain {parts[4]}")
    if len(parts) == 4 and method == "GET":
        row = await conn.fetchrow(
            """SELECT s.*, a.status AS attach_status, a.id AS attachment_id
               FROM ov_storage_domain_attachments a
               JOIN ov_storage_domains s ON s.id=a.storage_domain_id
               WHERE a.datacenter_id=$1::uuid AND a.storage_domain_id=$2::uuid""",
            dc_id,
            parts[3],
        )
        if row is None:
            raise OVirtError("NotFound", "attached storage domain not found", status_code=404)
        return respond(request, element="storage_domain", data=storage_domain_entity(row))
    if len(parts) == 4 and method == "DELETE":
        await conn.execute(
            """DELETE FROM ov_storage_domain_attachments
               WHERE storage_domain_id=$1::uuid AND datacenter_id=$2::uuid""",
            parts[3],
            dc_id,
        )
        return Response(status_code=200)
    raise OVirtError("NotFound", "attached storagedomains", status_code=404)


async def _handle_clusters(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_clusters ORDER BY name")
        return respond(
            request, element="cluster", collection="clusters", data=[cluster_entity(r) for r in rows]
        )
    if len(parts) == 1 and method == "POST":
        body = unwrap_entity(payload, "cluster")
        cid = uuid4()
        dc = body.get("data_center") or {}
        dc_id = dc.get("id") if isinstance(dc, dict) else None
        if not dc_id:
            dc_id = await conn.fetchval("SELECT id FROM ov_datacenters LIMIT 1")
        await conn.execute(
            """INSERT INTO ov_clusters(id, datacenter_id, name, description, cpu_type)
               VALUES($1,$2,$3,$4,$5)""",
            cid,
            dc_id,
            str(body.get("name") or f"cluster-{cid.hex[:6]}"),
            str(body.get("description") or ""),
            str(
                (body.get("cpu") or {}).get("type")
                or await option_value(conn, OPT_DEFAULT_CLUSTER_CPU_TYPE)
            ),
        )
        row = await conn.fetchrow("SELECT * FROM ov_clusters WHERE id=$1", cid)
        return respond(request, element="cluster", data=cluster_entity(row), status_code=201)
    cluster_id = parts[1]
    if len(parts) == 2 and method == "GET":
        row = await conn.fetchrow("SELECT * FROM ov_clusters WHERE id=$1::uuid", cluster_id)
        if row is None:
            raise OVirtError("NotFound", "cluster not found", status_code=404)
        return respond(request, element="cluster", data=cluster_entity(row))
    if len(parts) == 2 and method == "PUT":
        body = unwrap_entity(payload, "cluster")
        await conn.execute(
            "UPDATE ov_clusters SET name=COALESCE($2,name), description=COALESCE($3,description) WHERE id=$1::uuid",
            cluster_id,
            body.get("name"),
            body.get("description"),
        )
        row = await conn.fetchrow("SELECT * FROM ov_clusters WHERE id=$1::uuid", cluster_id)
        return respond(request, element="cluster", data=cluster_entity(row))
    if len(parts) == 2 and method == "DELETE":
        await conn.execute("DELETE FROM ov_clusters WHERE id=$1::uuid", cluster_id)
        return Response(status_code=200)
    if len(parts) == 3 and method == "POST":
        return await respond_action(request, conn, description=f"Cluster {parts[2]}")
    if len(parts) >= 3 and parts[2] == "affinitygroups":
        if method == "GET" and len(parts) == 3:
            rows = await conn.fetch(
                "SELECT * FROM ov_affinity_groups WHERE cluster_id=$1::uuid ORDER BY name",
                cluster_id,
            )
            items = [_affinity_group_entity(r, cluster_id) for r in rows]
            return respond(
                request, element="affinity_group", collection="affinity_groups", data=items
            )
        if method == "POST" and len(parts) == 3:
            body = unwrap_entity(payload, "affinity_group")
            aid = uuid4()
            await conn.execute(
                """INSERT INTO ov_affinity_groups(id, cluster_id, name, enforcing, positive)
                   VALUES($1,$2::uuid,$3,$4,$5)""",
                aid,
                cluster_id,
                str(body.get("name") or f"ag-{aid.hex[:6]}"),
                bool(body.get("enforcing", True)),
                bool(body.get("positive", True)),
            )
            r = await conn.fetchrow(
                "SELECT * FROM ov_affinity_groups WHERE id=$1 AND cluster_id=$2::uuid",
                aid,
                cluster_id,
            )
            return respond(
                request,
                element="affinity_group",
                data=_affinity_group_entity(r, cluster_id),
                status_code=201,
            )
        if method == "GET" and len(parts) == 4:
            r = await conn.fetchrow(
                "SELECT * FROM ov_affinity_groups WHERE id=$1::uuid AND cluster_id=$2::uuid",
                parts[3],
                cluster_id,
            )
            if r is None:
                raise OVirtError("NotFound", "affinity group not found", status_code=404)
            return respond(
                request,
                element="affinity_group",
                data=_affinity_group_entity(r, cluster_id),
            )
        if method == "DELETE" and len(parts) == 4:
            await conn.execute(
                "DELETE FROM ov_affinity_groups WHERE id=$1::uuid AND cluster_id=$2::uuid",
                parts[3],
                cluster_id,
            )
            return Response(status_code=200)
    if len(parts) >= 3 and parts[2] == "networks":
        return await _cluster_networks(request, conn, method, parts, payload)
    from app.ovirt.schema_engine import handle_subcollection

    if len(parts) >= 3:
        return await handle_subcollection(
            request, conn, method, "clusters", cluster_id, parts[2], parts[3:], payload
        )
    raise OVirtError("NotFound", "clusters path", status_code=404)


async def _cluster_networks(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    """Cluster networks = networks of the cluster's datacenter (Engine model)."""

    del payload
    cluster_id = parts[1]
    cluster = await conn.fetchrow("SELECT * FROM ov_clusters WHERE id=$1::uuid", cluster_id)
    if cluster is None:
        raise OVirtError("NotFound", "cluster not found", status_code=404)
    dc_id = cluster["datacenter_id"]
    if len(parts) == 3 and method == "GET":
        rows = await conn.fetch(
            "SELECT * FROM ov_networks WHERE datacenter_id=$1::uuid ORDER BY name", dc_id
        )
        return respond(
            request,
            element="network",
            collection="networks",
            data=[network_entity(r) for r in rows],
        )
    if len(parts) == 4 and method == "GET":
        row = await conn.fetchrow(
            "SELECT * FROM ov_networks WHERE id=$1::uuid AND datacenter_id=$2::uuid",
            parts[3],
            dc_id,
        )
        if row is None:
            raise OVirtError("NotFound", "network not found", status_code=404)
        return respond(request, element="network", data=network_entity(row))
    raise OVirtError("NotFound", "cluster networks path", status_code=404)


async def _handle_networks(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_networks ORDER BY name")
        return respond(
            request, element="network", collection="networks", data=[network_entity(r) for r in rows]
        )
    if len(parts) == 1 and method == "POST":
        body = unwrap_entity(payload, "network")
        nid = uuid4()
        dc = body.get("data_center") or {}
        dc_id = dc.get("id") if isinstance(dc, dict) else None
        if not dc_id:
            dc_id = await conn.fetchval("SELECT id FROM ov_datacenters LIMIT 1")
        await conn.execute(
            """INSERT INTO ov_networks(id, datacenter_id, name, description, vlan_id, stp)
               VALUES($1,$2,$3,$4,$5,$6)""",
            nid,
            dc_id,
            str(body.get("name") or f"net-{nid.hex[:6]}"),
            str(body.get("description") or ""),
            (body.get("vlan") or {}).get("id") if isinstance(body.get("vlan"), dict) else None,
            bool(body.get("stp", False)),
        )
        row = await conn.fetchrow("SELECT * FROM ov_networks WHERE id=$1", nid)
        return respond(request, element="network", data=network_entity(row), status_code=201)
    net_id = parts[1]
    if len(parts) == 2 and method == "GET":
        row = await conn.fetchrow("SELECT * FROM ov_networks WHERE id=$1::uuid", net_id)
        if row is None:
            raise OVirtError("NotFound", "network not found", status_code=404)
        return respond(request, element="network", data=network_entity(row))
    if len(parts) == 2 and method == "PUT":
        body = unwrap_entity(payload, "network")
        await conn.execute(
            "UPDATE ov_networks SET name=COALESCE($2,name), description=COALESCE($3,description) WHERE id=$1::uuid",
            net_id,
            body.get("name"),
            body.get("description"),
        )
        row = await conn.fetchrow("SELECT * FROM ov_networks WHERE id=$1::uuid", net_id)
        return respond(request, element="network", data=network_entity(row))
    if len(parts) == 2 and method == "DELETE":
        await conn.execute("DELETE FROM ov_networks WHERE id=$1::uuid", net_id)
        return Response(status_code=200)
    if len(parts) >= 3 and parts[2] == "vnicprofiles":
        if method == "GET" and len(parts) == 3:
            rows = await conn.fetch(
                "SELECT * FROM ov_vnic_profiles WHERE network_id=$1::uuid ORDER BY name", net_id
            )
            items = [
                {
                    "id": str(r["id"]),
                    "href": f"/ovirt-engine/api/vnicprofiles/{r['id']}",
                    "name": r["name"],
                    "network": {"id": net_id, "href": f"/ovirt-engine/api/networks/{net_id}"},
                }
                for r in rows
            ]
            return respond(
                request, element="vnic_profile", collection="vnic_profiles", data=items
            )
        if method == "GET" and len(parts) == 4:
            r = await conn.fetchrow(
                "SELECT * FROM ov_vnic_profiles WHERE id=$1::uuid AND network_id=$2::uuid",
                parts[3],
                net_id,
            )
            if r is None:
                raise OVirtError("NotFound", "vnic profile not found", status_code=404)
            return respond(
                request,
                element="vnic_profile",
                data={
                    "id": str(r["id"]),
                    "href": f"/ovirt-engine/api/vnicprofiles/{r['id']}",
                    "name": r["name"],
                    "network": {"id": net_id, "href": f"/ovirt-engine/api/networks/{net_id}"},
                },
            )
        if method == "DELETE" and len(parts) == 4:
            await conn.execute(
                "DELETE FROM ov_vnic_profiles WHERE id=$1::uuid AND network_id=$2::uuid",
                parts[3],
                net_id,
            )
            return Response(status_code=200)
    from app.ovirt.schema_engine import handle_subcollection

    if len(parts) >= 3:
        return await handle_subcollection(
            request, conn, method, "networks", net_id, parts[2], parts[3:], payload
        )
    raise OVirtError("NotFound", "networks path", status_code=404)


async def _handle_vnicprofiles(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_vnic_profiles ORDER BY name")
        items = [
            {
                "id": str(r["id"]),
                "href": f"/ovirt-engine/api/vnicprofiles/{r['id']}",
                "name": r["name"],
                "network": {
                    "id": str(r["network_id"]),
                    "href": f"/ovirt-engine/api/networks/{r['network_id']}",
                },
            }
            for r in rows
        ]
        return respond(request, element="vnic_profile", collection="vnic_profiles", data=items)
    if len(parts) == 1 and method == "POST":
        body = unwrap_entity(payload, "vnic_profile")
        pid = uuid4()
        net = body.get("network") or {}
        net_id = net.get("id") if isinstance(net, dict) else None
        if not net_id:
            net_id = await conn.fetchval("SELECT id FROM ov_networks LIMIT 1")
        await conn.execute(
            "INSERT INTO ov_vnic_profiles(id, network_id, name) VALUES($1,$2,$3)",
            pid,
            net_id,
            str(body.get("name") or f"profile-{pid.hex[:6]}"),
        )
        r = await conn.fetchrow("SELECT * FROM ov_vnic_profiles WHERE id=$1", pid)
        return respond(
            request,
            element="vnic_profile",
            data=_vnic_profile_entity(r),
            status_code=201,
        )
    if len(parts) == 2 and method == "GET":
        r = await conn.fetchrow("SELECT * FROM ov_vnic_profiles WHERE id=$1::uuid", parts[1])
        if r is None:
            raise OVirtError("NotFound", "vnic profile not found", status_code=404)
        return respond(request, element="vnic_profile", data=_vnic_profile_entity(r))
    if len(parts) == 2 and method == "DELETE":
        await conn.execute("DELETE FROM ov_vnic_profiles WHERE id=$1::uuid", parts[1])
        return Response(status_code=200)
    raise OVirtError("NotFound", "vnicprofiles path", status_code=404)


async def _handle_storage_domains(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_storage_domains ORDER BY name")
        return respond(
            request,
            element="storage_domain",
            collection="storage_domains",
            data=[storage_domain_entity(r) for r in rows],
        )
    if len(parts) == 1 and method == "POST":
        body = unwrap_entity(payload, "storage_domain")
        sid = uuid4()
        storage = body.get("storage") or {}
        await conn.execute(
            """INSERT INTO ov_storage_domains(id, name, type, storage_type, status, available, used)
               VALUES($1,$2,$3,$4,$5,$6,0)""",
            sid,
            str(body.get("name") or f"sd-{sid.hex[:6]}"),
            str(body.get("type") or await option_value(conn, OPT_DEFAULT_SD_TYPE)),
            str(storage.get("type") or await option_value(conn, OPT_DEFAULT_STORAGE_TYPE)),
            await option_value(conn, OPT_DEFAULT_SD_STATUS),
            int(body.get("available") or await option_int(conn, OPT_DEFAULT_SD_AVAILABLE)),
        )
        row = await conn.fetchrow("SELECT * FROM ov_storage_domains WHERE id=$1", sid)
        return respond(
            request, element="storage_domain", data=storage_domain_entity(row), status_code=201
        )
    sd_id = parts[1]
    if len(parts) == 2 and method == "GET":
        row = await conn.fetchrow("SELECT * FROM ov_storage_domains WHERE id=$1::uuid", sd_id)
        if row is None:
            raise OVirtError("NotFound", "storage domain not found", status_code=404)
        return respond(request, element="storage_domain", data=storage_domain_entity(row))
    if len(parts) == 2 and method == "PUT":
        body = unwrap_entity(payload, "storage_domain")
        await conn.execute(
            "UPDATE ov_storage_domains SET name=COALESCE($2,name) WHERE id=$1::uuid",
            sd_id,
            body.get("name"),
        )
        row = await conn.fetchrow("SELECT * FROM ov_storage_domains WHERE id=$1::uuid", sd_id)
        return respond(request, element="storage_domain", data=storage_domain_entity(row))
    if len(parts) == 2 and method == "DELETE":
        await conn.execute("DELETE FROM ov_storage_domains WHERE id=$1::uuid", sd_id)
        return Response(status_code=200)
    if len(parts) == 3 and method == "POST":
        return await respond_action(request, conn, description=f"Storage domain {parts[2]}")
    if len(parts) >= 3 and parts[2] == "disks":
        if method == "GET" and len(parts) == 3:
            rows = await conn.fetch(
                "SELECT * FROM ov_disks WHERE storage_domain_id=$1::uuid ORDER BY name", sd_id
            )
            return respond(
                request, element="disk", collection="disks", data=[disk_entity(r) for r in rows]
            )
        if method == "GET" and len(parts) == 4:
            row = await conn.fetchrow(
                "SELECT * FROM ov_disks WHERE id=$1::uuid AND storage_domain_id=$2::uuid",
                parts[3],
                sd_id,
            )
            if row is None:
                raise OVirtError("NotFound", "disk not found on storage domain", status_code=404)
            return respond(request, element="disk", data=disk_entity(row))
    from app.ovirt.schema_engine import handle_subcollection

    if len(parts) >= 3:
        return await handle_subcollection(
            request, conn, method, "storagedomains", sd_id, parts[2], parts[3:], payload
        )
    raise OVirtError("NotFound", "storagedomains path", status_code=404)


async def _handle_storage_connections(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_storage_connections ORDER BY address")
        items = [
            {
                "id": str(r["id"]),
                "href": f"/ovirt-engine/api/storageconnections/{r['id']}",
                "type": r["type"],
                "address": r["address"],
                "path": r["path"],
            }
            for r in rows
        ]
        return respond(
            request, element="storage_connection", collection="storage_connections", data=items
        )
    if len(parts) == 1 and method == "POST":
        body = unwrap_entity(payload, "storage_connection")
        cid = uuid4()
        await conn.execute(
            "INSERT INTO ov_storage_connections(id, type, address, path) VALUES($1,$2,$3,$4)",
            cid,
            str(
                body.get("type")
                or await option_value(conn, OPT_DEFAULT_STORAGE_CONNECTION_TYPE)
            ),
            str(body.get("address") or ""),
            str(body.get("path") or ""),
        )
        r = await conn.fetchrow("SELECT * FROM ov_storage_connections WHERE id=$1", cid)
        return respond(
            request,
            element="storage_connection",
            data=_storage_connection_entity(r),
            status_code=201,
        )
    if len(parts) == 2 and method == "GET":
        r = await conn.fetchrow("SELECT * FROM ov_storage_connections WHERE id=$1::uuid", parts[1])
        if r is None:
            raise OVirtError("NotFound", "storage connection not found", status_code=404)
        return respond(request, element="storage_connection", data=_storage_connection_entity(r))
    if len(parts) == 2 and method == "DELETE":
        await conn.execute("DELETE FROM ov_storage_connections WHERE id=$1::uuid", parts[1])
        return Response(status_code=200)
    raise OVirtError("NotFound", "storageconnections path", status_code=404)


async def _handle_templates(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_templates ORDER BY name")
        return respond(
            request,
            element="template",
            collection="templates",
            data=[template_entity(r) for r in rows],
        )
    if len(parts) == 1 and method == "POST":
        body = unwrap_entity(payload, "template")
        tid = uuid4()
        vm = body.get("vm") or {}
        cluster_id = None
        if isinstance(vm, dict) and vm.get("id"):
            cluster_id = await conn.fetchval(
                "SELECT cluster_id FROM ov_vms WHERE id=$1::uuid", vm["id"]
            )
        if not cluster_id:
            cluster_id = await conn.fetchval("SELECT id FROM ov_clusters LIMIT 1")
        await conn.execute(
            """INSERT INTO ov_templates(id, cluster_id, name, description, memory)
               VALUES($1,$2,$3,$4,$5)""",
            tid,
            cluster_id,
            str(body.get("name") or f"tpl-{tid.hex[:6]}"),
            str(body.get("description") or ""),
            int(body.get("memory") or await option_int(conn, OPT_DEFAULT_VM_MEMORY)),
        )
        row = await conn.fetchrow("SELECT * FROM ov_templates WHERE id=$1", tid)
        return respond(request, element="template", data=template_entity(row), status_code=201)
    tid = parts[1]
    if len(parts) == 2 and method == "GET":
        row = await conn.fetchrow("SELECT * FROM ov_templates WHERE id=$1::uuid", tid)
        if row is None:
            raise OVirtError("NotFound", "template not found", status_code=404)
        return respond(request, element="template", data=template_entity(row))
    if len(parts) == 2 and method == "DELETE":
        await conn.execute("DELETE FROM ov_templates WHERE id=$1::uuid", tid)
        return Response(status_code=200)
    if len(parts) == 3 and method == "POST":
        return await respond_action(request, conn, description=f"Template {parts[2]}")
    from app.ovirt.schema_engine import handle_subcollection

    if len(parts) >= 3:
        return await handle_subcollection(
            request, conn, method, "templates", tid, parts[2], parts[3:], payload
        )
    raise OVirtError("NotFound", "templates path", status_code=404)


async def _handle_users(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch(
            """SELECT u.*, d.name AS domain_name FROM ov_users u
               JOIN ov_domains d ON d.id=u.domain_id ORDER BY u.name"""
        )
        return respond(
            request, element="user", collection="users", data=[user_entity(r) for r in rows]
        )
    if len(parts) == 2 and method == "GET":
        row = await conn.fetchrow(
            """SELECT u.*, d.name AS domain_name FROM ov_users u
               JOIN ov_domains d ON d.id=u.domain_id WHERE u.id=$1::uuid""",
            parts[1],
        )
        if row is None:
            raise OVirtError("NotFound", "user not found", status_code=404)
        return respond(request, element="user", data=user_entity(row))
    if len(parts) >= 3 and parts[2] == "permissions" and method == "GET":
        user_id = parts[1]
        if len(parts) == 3:
            rows = await conn.fetch(
                """SELECT p.*, r.name AS role_name, u.name AS user_name
                   FROM ov_permissions p
                   JOIN ov_roles r ON r.id = p.role_id
                   LEFT JOIN ov_users u ON u.id = p.user_id
                   WHERE p.user_id=$1::uuid
                   ORDER BY r.name""",
                user_id,
            )
            items = [_permission_entity(r) for r in rows]
            return respond(request, element="permission", collection="permissions", data=items)
        if len(parts) == 4:
            r = await conn.fetchrow(
                """SELECT p.*, r.name AS role_name, u.name AS user_name
                   FROM ov_permissions p
                   JOIN ov_roles r ON r.id = p.role_id
                   LEFT JOIN ov_users u ON u.id = p.user_id
                   WHERE p.id=$1::uuid AND p.user_id=$2::uuid""",
                parts[3],
                user_id,
            )
            if r is None:
                raise OVirtError("NotFound", "permission not found", status_code=404)
            return respond(request, element="permission", data=_permission_entity(r))
    if len(parts) >= 3 and parts[2] == "roles" and method == "GET" and len(parts) == 3:
        rows = await conn.fetch(
            """SELECT DISTINCT r.*
               FROM ov_permissions p
               JOIN ov_roles r ON r.id = p.role_id
               WHERE p.user_id=$1::uuid
               ORDER BY r.name""",
            parts[1],
        )
        items = [
            {
                "id": str(r["id"]),
                "href": f"/ovirt-engine/api/roles/{r['id']}",
                "name": r["name"],
            }
            for r in rows
        ]
        return respond(request, element="role", collection="roles", data=items)
    from app.ovirt.schema_engine import handle_subcollection

    if len(parts) >= 3:
        return await handle_subcollection(
            request, conn, method, "users", parts[1], parts[2], parts[3:], payload
        )
    raise OVirtError("NotFound", "users path", status_code=404)


def _permission_entity(r: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": str(r["id"]),
        "href": f"/ovirt-engine/api/permissions/{r['id']}",
        "role": {"id": str(r["role_id"]), "name": r["role_name"]},
        "object": {"type": r["object_type"]},
    }
    if r["user_id"] is not None:
        item["user"] = {"id": str(r["user_id"]), "name": r["user_name"]}
    return item


def _group_entity(r: Any) -> dict[str, Any]:
    gid = str(r["id"])
    return {
        "id": gid,
        "href": f"/ovirt-engine/api/groups/{gid}",
        "name": r["name"],
        "domain": {"id": str(r["domain_id"]), "href": f"/ovirt-engine/api/domains/{r['domain_id']}"},
        "link": [
            {"rel": "permissions", "href": f"/ovirt-engine/api/groups/{gid}/permissions"},
            {"rel": "tags", "href": f"/ovirt-engine/api/groups/{gid}/tags"},
        ],
    }


async def _handle_groups(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_groups ORDER BY name")
        return respond(
            request,
            element="group",
            collection="groups",
            data=[_group_entity(r) for r in rows],
        )
    if len(parts) == 1 and method == "POST":
        body = unwrap_entity(payload, "group")
        gid = uuid4()
        domain = body.get("domain") or {}
        domain_id = domain.get("id") if isinstance(domain, dict) else None
        if not domain_id:
            domain_id = await conn.fetchval("SELECT id FROM ov_domains ORDER BY name LIMIT 1")
        if not domain_id:
            raise OVirtError("BadRequest", "domain is required", status_code=400)
        await conn.execute(
            "INSERT INTO ov_groups(id, domain_id, name) VALUES($1,$2::uuid,$3)",
            gid,
            domain_id,
            str(body.get("name") or f"group-{gid.hex[:6]}"),
        )
        row = await conn.fetchrow("SELECT * FROM ov_groups WHERE id=$1", gid)
        return respond(request, element="group", data=_group_entity(row), status_code=201)
    group_id = parts[1]
    if len(parts) == 2 and method == "GET":
        row = await conn.fetchrow("SELECT * FROM ov_groups WHERE id=$1::uuid", group_id)
        if row is None:
            raise OVirtError("NotFound", "group not found", status_code=404)
        return respond(request, element="group", data=_group_entity(row))
    if len(parts) == 2 and method == "PUT":
        body = unwrap_entity(payload, "group")
        await conn.execute(
            "UPDATE ov_groups SET name=COALESCE($2,name) WHERE id=$1::uuid",
            group_id,
            body.get("name"),
        )
        row = await conn.fetchrow("SELECT * FROM ov_groups WHERE id=$1::uuid", group_id)
        if row is None:
            raise OVirtError("NotFound", "group not found", status_code=404)
        return respond(request, element="group", data=_group_entity(row))
    if len(parts) == 2 and method == "DELETE":
        await conn.execute("DELETE FROM ov_groups WHERE id=$1::uuid", group_id)
        return Response(status_code=200)
    if len(parts) >= 3:
        from app.ovirt.schema_engine import handle_subcollection

        return await handle_subcollection(
            request, conn, method, "groups", group_id, parts[2], parts[3:], payload
        )
    raise OVirtError("NotFound", "groups path", status_code=404)


async def _handle_domains(
    request: Request, conn: Connection, method: str, parts: list[str]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_domains ORDER BY name")
        items = [
            {
                "id": str(r["id"]),
                "href": f"/ovirt-engine/api/domains/{r['id']}",
                "name": r["name"],
            }
            for r in rows
        ]
        return respond(request, element="domain", collection="domains", data=items)
    if len(parts) == 2 and method == "GET":
        row = await conn.fetchrow("SELECT * FROM ov_domains WHERE id=$1::uuid", parts[1])
        if row is None:
            raise OVirtError("NotFound", "domain not found", status_code=404)
        return respond(
            request,
            element="domain",
            data={
                "id": str(row["id"]),
                "href": f"/ovirt-engine/api/domains/{row['id']}",
                "name": row["name"],
            },
        )
    if len(parts) >= 3 and method == "GET":
        domain_id = parts[1]
        domain = await conn.fetchrow("SELECT id FROM ov_domains WHERE id=$1::uuid", domain_id)
        if domain is None:
            raise OVirtError("NotFound", "domain not found", status_code=404)
        if parts[2] == "users":
            if len(parts) == 3:
                rows = await conn.fetch(
                    """SELECT u.*, d.name AS domain_name FROM ov_users u
                       JOIN ov_domains d ON d.id=u.domain_id
                       WHERE u.domain_id=$1::uuid ORDER BY u.name""",
                    domain_id,
                )
                return respond(
                    request, element="user", collection="users", data=[user_entity(r) for r in rows]
                )
            if len(parts) == 4:
                row = await conn.fetchrow(
                    """SELECT u.*, d.name AS domain_name FROM ov_users u
                       JOIN ov_domains d ON d.id=u.domain_id
                       WHERE u.id=$1::uuid AND u.domain_id=$2::uuid""",
                    parts[3],
                    domain_id,
                )
                if row is None:
                    raise OVirtError("NotFound", "user not found", status_code=404)
                return respond(request, element="user", data=user_entity(row))
        if parts[2] == "groups":
            if len(parts) == 3:
                rows = await conn.fetch(
                    "SELECT * FROM ov_groups WHERE domain_id=$1::uuid ORDER BY name", domain_id
                )
                items = [
                    {
                        "id": str(r["id"]),
                        "href": f"/ovirt-engine/api/groups/{r['id']}",
                        "name": r["name"],
                    }
                    for r in rows
                ]
                return respond(request, element="group", collection="groups", data=items)
            if len(parts) == 4:
                r = await conn.fetchrow(
                    "SELECT * FROM ov_groups WHERE id=$1::uuid AND domain_id=$2::uuid",
                    parts[3],
                    domain_id,
                )
                if r is None:
                    raise OVirtError("NotFound", "group not found", status_code=404)
                return respond(
                    request,
                    element="group",
                    data={
                        "id": str(r["id"]),
                        "href": f"/ovirt-engine/api/groups/{r['id']}",
                        "name": r["name"],
                    },
                )
    raise OVirtError("NotFound", "domains path", status_code=404)


async def _handle_permissions(
    request: Request, conn: Connection, method: str, parts: list[str]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch(
            """SELECT p.*, r.name AS role_name, u.name AS user_name
               FROM ov_permissions p
               JOIN ov_roles r ON r.id = p.role_id
               LEFT JOIN ov_users u ON u.id = p.user_id
               ORDER BY r.name, u.name NULLS LAST"""
        )
        items = []
        for r in rows:
            item: dict[str, Any] = {
                "id": str(r["id"]),
                "href": f"/ovirt-engine/api/permissions/{r['id']}",
                "role": {"id": str(r["role_id"]), "name": r["role_name"]},
                "object": {"type": r["object_type"]},
            }
            if r["user_id"] is not None:
                item["user"] = {"id": str(r["user_id"]), "name": r["user_name"]}
            items.append(item)
        return respond(request, element="permission", collection="permissions", data=items)
    if len(parts) == 2 and method == "GET":
        r = await conn.fetchrow(
            """SELECT p.*, r.name AS role_name, u.name AS user_name
               FROM ov_permissions p
               JOIN ov_roles r ON r.id = p.role_id
               LEFT JOIN ov_users u ON u.id = p.user_id
               WHERE p.id=$1::uuid""",
            parts[1],
        )
        if r is None:
            raise OVirtError("NotFound", "permission not found", status_code=404)
        data: dict[str, Any] = {
            "id": str(r["id"]),
            "href": f"/ovirt-engine/api/permissions/{r['id']}",
            "role": {"id": str(r["role_id"]), "name": r["role_name"]},
            "object": {"type": r["object_type"]},
        }
        if r["user_id"] is not None:
            data["user"] = {"id": str(r["user_id"]), "name": r["user_name"]}
        return respond(request, element="permission", data=data)
    raise OVirtError("NotFound", "permissions path", status_code=404)


async def _handle_jobs(
    request: Request, conn: Connection, method: str, parts: list[str], payload: dict[str, Any]
) -> Response:
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch("SELECT * FROM ov_jobs ORDER BY started DESC LIMIT 200")
        items = [job_entity(r) for r in rows]
        return respond(request, element="job", collection="jobs", data=items)
    if len(parts) == 2 and method == "GET":
        r = await conn.fetchrow("SELECT * FROM ov_jobs WHERE id=$1::uuid", parts[1])
        if r is None:
            raise OVirtError("NotFound", "job not found", status_code=404)
        return respond(request, element="job", data=job_entity(r))
    if len(parts) == 3 and parts[2] == "steps" and method == "GET":
        rows = await conn.fetch(
            "SELECT * FROM ov_job_steps WHERE job_id=$1::uuid ORDER BY number", parts[1]
        )
        items = [
            {
                "id": str(r["id"]),
                "description": r["description"],
                "status": r["status"],
                "type": r["type"],
            }
            for r in rows
        ]
        return respond(request, element="step", collection="steps", data=items)
    raise OVirtError("NotFound", "jobs path", status_code=404)


async def _handle_events(
    request: Request, conn: Connection, method: str, parts: list[str]
) -> Response:
    if len(parts) == 1 and method == "GET":
        max_r = int(request.query_params.get("max") or 100)
        rows = await conn.fetch(
            "SELECT * FROM ov_events ORDER BY id DESC LIMIT $1", max_r
        )
        items = [
            {
                "id": str(r["id"]),
                "href": f"/ovirt-engine/api/events/{r['id']}",
                "code": r["code"],
                "severity": r["severity"],
                "description": r["description"],
                "time": r["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            }
            for r in rows
        ]
        return respond(request, element="event", collection="events", data=items)
    if len(parts) == 2 and method == "GET":
        r = await conn.fetchrow("SELECT * FROM ov_events WHERE id=$1::bigint", int(parts[1]))
        if r is None:
            raise OVirtError("NotFound", "event not found", status_code=404)
        return respond(
            request,
            element="event",
            data={
                "id": str(r["id"]),
                "code": r["code"],
                "severity": r["severity"],
                "description": r["description"],
            },
        )
    raise OVirtError("NotFound", "events path", status_code=404)


def _row_entity(r: Any, collection: str, fields: list[str]) -> dict[str, Any]:
    item = {"id": str(r["id"]), "href": f"/ovirt-engine/api/{collection}/{r['id']}"}
    for f in fields:
        if f in r.keys():
            item[f] = r[f]
    return item


def _affinity_group_entity(r: Any, cluster_id: str) -> dict[str, Any]:
    return {
        "id": str(r["id"]),
        "href": f"/ovirt-engine/api/clusters/{cluster_id}/affinitygroups/{r['id']}",
        "name": r["name"],
        "description": r["description"] or "",
        "enforcing": bool(r["enforcing"]),
        "positive": bool(r["positive"]),
    }


def _vnic_profile_entity(r: Any) -> dict[str, Any]:
    return {
        "id": str(r["id"]),
        "href": f"/ovirt-engine/api/vnicprofiles/{r['id']}",
        "name": r["name"],
        "network": {
            "id": str(r["network_id"]),
            "href": f"/ovirt-engine/api/networks/{r['network_id']}",
        },
    }


def _storage_connection_entity(r: Any) -> dict[str, Any]:
    return {
        "id": str(r["id"]),
        "href": f"/ovirt-engine/api/storageconnections/{r['id']}",
        "type": r["type"],
        "address": r["address"],
        "path": r["path"],
    }


async def _handle_simple_table(
    request: Request,
    conn: Connection,
    method: str,
    parts: list[str],
    table: str,
    collection: str,
    element: str,
    fields: list[str],
    payload: dict[str, Any] | None = None,
) -> Response:
    payload = payload or {}
    if len(parts) == 1 and method == "GET":
        rows = await conn.fetch(f"SELECT * FROM {table} ORDER BY name")  # noqa: S608
        items = [_row_entity(r, collection, fields) for r in rows]
        return respond(request, element=element, collection=collection, data=items)
    if len(parts) == 1 and method == "POST":
        body = unwrap_entity(payload, element)
        oid = uuid4()
        cols = ["id", *fields]
        values: list[Any] = [oid]
        for f in fields:
            values.append(body.get(f) or ("" if f != "name" else f"{element}-{oid.hex[:6]}"))
        placeholders = ", ".join(f"${i}" for i in range(1, len(cols) + 1))
        await conn.execute(
            f"INSERT INTO {table}({', '.join(cols)}) VALUES({placeholders})",
            *values,
        )
        r = await conn.fetchrow(f"SELECT * FROM {table} WHERE id=$1", oid)  # noqa: S608
        return respond(
            request, element=element, data=_row_entity(r, collection, fields), status_code=201
        )
    if len(parts) == 2 and method == "GET":
        r = await conn.fetchrow(f"SELECT * FROM {table} WHERE id=$1::uuid", parts[1])  # noqa: S608
        if r is None:
            raise OVirtError("NotFound", f"{element} not found", status_code=404)
        return respond(request, element=element, data=_row_entity(r, collection, fields))
    if len(parts) == 2 and method == "PUT":
        body = unwrap_entity(payload, element)
        sets = []
        values: list[Any] = [parts[1]]
        for f in fields:
            if f in body:
                values.append(body[f])
                sets.append(f"{f}=${len(values)}")
        if sets:
            await conn.execute(
                f"UPDATE {table} SET {', '.join(sets)} WHERE id=$1::uuid",  # noqa: S608
                *values,
            )
        r = await conn.fetchrow(f"SELECT * FROM {table} WHERE id=$1::uuid", parts[1])  # noqa: S608
        return respond(request, element=element, data=_row_entity(r, collection, fields))
    if len(parts) == 2 and method == "DELETE":
        await conn.execute(f"DELETE FROM {table} WHERE id=$1::uuid", parts[1])  # noqa: S608
        return Response(status_code=200)
    if len(parts) >= 3:
        from app.ovirt.schema_engine import handle_subcollection

        return await handle_subcollection(
            request, conn, method, collection, parts[1], parts[2], parts[3:], payload
        )
    raise OVirtError("NotFound", f"{collection} path", status_code=404)
