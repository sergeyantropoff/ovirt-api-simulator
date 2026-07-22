"""Generic surface-complete CRUD backed by ov_api_objects for undeclared collections."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from asyncpg import Connection
from fastapi import Request, Response

from app.ovirt.errors import OVirtError
from app.ovirt.repr import generic_entity
from app.ovirt.serialize import respond, unwrap_entity

# Map collection path segment → (element singular, default status)
_COLLECTIONS: dict[str, tuple[str, str]] = {
    "affinitylabels": ("affinity_label", "ok"),
    "bookmarks": ("bookmark", "ok"),
    "clusterlevels": ("cluster_level", "ok"),
    "domains": ("domain", "ok"),
    "externalhostproviders": ("external_host_provider", "ok"),
    "groups": ("group", "ok"),
    "icons": ("icon", "ok"),
    "instancetypes": ("instance_type", "ok"),
    "katelloerrata": ("katello_erratum", "ok"),
    "macpools": ("mac_pool", "ok"),
    "networkfilters": ("network_filter", "ok"),
    "openstackimageproviders": ("openstack_image_provider", "ok"),
    "openstacknetworkproviders": ("openstack_network_provider", "ok"),
    "openstackvolumeproviders": ("openstack_volume_provider", "ok"),
    "operatingsystems": ("operating_system", "ok"),
    "permissions": ("permission", "ok"),
    "roles": ("role", "ok"),
    "schedulingpolicies": ("scheduling_policy", "ok"),
    "schedulingpolicyunits": ("scheduling_policy_unit", "ok"),
    "tags": ("tag", "ok"),
    "vmpools": ("vm_pool", "ok"),
    "imagetransfers": ("image_transfer", "ok"),
    "options": ("engine_option", "ok"),
    "networklabels": ("network_label", "ok"),
    "cpuprofiles": ("cpu_profile", "ok"),
    "diskprofiles": ("disk_profile", "ok"),
    "diskattachments": ("disk_attachment", "ok"),
    "qoss": ("qos", "ok"),
    "iscsibonds": ("iscsi_bond", "ok"),
    "glustervolumes": ("gluster_volume", "ok"),
    "files": ("file", "ok"),
    "images": ("image", "ok"),
    "permits": ("permit", "ok"),
    "filters": ("filter", "ok"),
    "weights": ("weight", "ok"),
    "balances": ("balance", "ok"),
    "enabledfeatures": ("cluster_enabled_feature", "ok"),
    "cdroms": ("cdrom", "ok"),
    "graphicsconsoles": ("graphics_console", "ok"),
    "reporteddevices": ("reported_device", "ok"),
    "sessions": ("session", "ok"),
    "applications": ("application", "ok"),
    "watchdogs": ("watchdog", "ok"),
    "hostdevices": ("host_device", "ok"),
    "numanodes": ("numa_node", "ok"),
    "mediateddevices": ("vm_mediated_device", "ok"),
    "statistics": ("statistic", "ok"),
    "hooks": ("hook", "ok"),
    "devices": ("host_device", "ok"),
    "sshpublickeys": ("ssh_public_key", "ok"),
    "networkfilterparameters": ("network_filter_parameter", "ok"),
    "storage": ("host_storage", "ok"),
}


def _meta(collection: str) -> tuple[str, str]:
    return _COLLECTIONS.get(collection, (collection.rstrip("s") or "object", "ok"))


async def handle_generic(
    request: Request,
    conn: Connection,
    method: str,
    parts: list[str],
    payload: dict[str, Any],
) -> Response:
    from app.ovirt.settings import OPT_DEFAULT_API_OBJECT_STATUS, option_value

    collection = parts[0]
    element, _catalog_status = _meta(collection)
    default_status = await option_value(conn, OPT_DEFAULT_API_OBJECT_STATUS)
    if len(parts) == 1:
        if method == "GET":
            rows = await conn.fetch(
                """SELECT * FROM ov_api_objects
                   WHERE collection=$1 AND parent_id IS NULL
                   ORDER BY name""",
                collection,
            )
            items = [generic_entity(collection, element, r) for r in rows]
            return respond(request, element=element, collection=collection, data=items)
        if method == "POST":
            body = unwrap_entity(payload, element)
            oid = uuid4()
            name = str(body.get("name") or f"{element}-{oid.hex[:8]}")
            await conn.execute(
                """INSERT INTO ov_api_objects(id, collection, name, status, data)
                   VALUES($1,$2,$3,$4,$5::jsonb)""",
                oid,
                collection,
                name,
                str(body.get("status") or default_status),
                json.dumps(body),
            )
            row = await conn.fetchrow("SELECT * FROM ov_api_objects WHERE id=$1", oid)
            return respond(
                request, element=element, data=generic_entity(collection, element, row), status_code=201
            )
    if len(parts) == 2:
        oid = parts[1]
        row = await conn.fetchrow(
            """SELECT * FROM ov_api_objects
               WHERE id=$1::uuid AND collection=$2 AND parent_id IS NULL""",
            oid,
            collection,
        )
        if method == "GET":
            if row is None:
                from app.ovirt.common import no_such

                raise no_such(element, oid)
            return respond(
                request,
                element=element,
                data=generic_entity(collection, element, row, entity_id=oid),
            )
        if method == "PUT":
            if row is None:
                from app.ovirt.common import no_such

                raise no_such(element, oid)
            body = unwrap_entity(payload, element)
            data = dict(json.loads(row["data"]) if isinstance(row["data"], str) else row["data"] or {})
            data.update(body)
            await conn.execute(
                """UPDATE ov_api_objects SET name=COALESCE($2,name), data=$3::jsonb, updated_at=now()
                   WHERE id=$1::uuid""",
                oid,
                body.get("name"),
                json.dumps(data),
            )
            row = await conn.fetchrow("SELECT * FROM ov_api_objects WHERE id=$1::uuid", oid)
            return respond(request, element=element, data=generic_entity(collection, element, row))
        if method == "DELETE":
            await conn.execute(
                """DELETE FROM ov_api_objects
                   WHERE id=$1::uuid AND collection=$2 AND parent_id IS NULL""",
                oid,
                collection,
            )
            return Response(status_code=200)
    if len(parts) == 3 and method == "POST":
        from app.ovirt.jobs import respond_action

        return await respond_action(
            request, conn, description=f"{collection} {parts[2]}"
        )
    if len(parts) >= 3:
        return await handle_subcollection(
            request, conn, method, collection, parts[1], parts[2], parts[3:], payload
        )
    raise OVirtError("NotFound", f"No handler for /{'/'.join(parts)}", status_code=404)


_PARENT_OBJECT_TYPE: dict[str, str] = {
    "vms": "vm",
    "hosts": "host",
    "disks": "disk",
    "datacenters": "data_center",
    "clusters": "cluster",
    "networks": "network",
    "storagedomains": "storage_domain",
    "templates": "template",
    "users": "user",
    "groups": "group",
    "vnicprofiles": "vnic_profile",
    "vmpools": "vm_pool",
}


async def handle_subcollection(
    request: Request,
    conn: Connection,
    method: str,
    parent_collection: str,
    parent_id: str,
    sub: str,
    rest: list[str],
    payload: dict[str, Any],
) -> Response:
    from app.ovirt.settings import OPT_DEFAULT_API_OBJECT_STATUS, option_value

    element, _catalog_status = _meta(sub)
    default_status = await option_value(conn, OPT_DEFAULT_API_OBJECT_STATUS)
    collection_key = sub
    if sub == "permissions" and method == "GET":
        object_type = _PARENT_OBJECT_TYPE.get(parent_collection, parent_collection.rstrip("s"))

        def _perm_item(r: Any) -> dict[str, Any]:
            return {
                "id": str(r["id"]),
                "href": f"/ovirt-engine/api/{parent_collection}/{parent_id}/permissions/{r['id']}",
                "role": {"id": str(r["role_id"]), "name": r["role_name"]},
                "object": {"type": r["object_type"], "id": str(parent_id)},
                **(
                    {"user": {"id": str(r["user_id"]), "name": r["user_name"]}}
                    if r["user_id"] is not None
                    else {}
                ),
            }

        if not rest:
            rows = await conn.fetch(
                """SELECT p.*, r.name AS role_name, u.name AS user_name
                   FROM ov_permissions p
                   JOIN ov_roles r ON r.id = p.role_id
                   LEFT JOIN ov_users u ON u.id = p.user_id
                   WHERE p.object_type=$1 AND p.object_id=$2::uuid
                   ORDER BY r.name""",
                object_type,
                parent_id,
            )
            return respond(
                request,
                element="permission",
                collection="permissions",
                data=[_perm_item(r) for r in rows],
            )
        if len(rest) == 1:
            r = await conn.fetchrow(
                """SELECT p.*, r.name AS role_name, u.name AS user_name
                   FROM ov_permissions p
                   JOIN ov_roles r ON r.id = p.role_id
                   LEFT JOIN ov_users u ON u.id = p.user_id
                   WHERE p.id=$1::uuid AND p.object_type=$2 AND p.object_id=$3::uuid""",
                rest[0],
                object_type,
                parent_id,
            )
            if r is None:
                raise OVirtError("NotFound", "permission not found", status_code=404)
            return respond(request, element="permission", data=_perm_item(r))
    if sub == "tags" and method == "GET":
        object_type = _PARENT_OBJECT_TYPE.get(parent_collection, parent_collection.rstrip("s"))
        if not rest:
            rows = await conn.fetch(
                """SELECT t.*
                   FROM ov_tag_assignments a
                   JOIN ov_tags t ON t.id = a.tag_id
                   WHERE a.object_type=$1 AND a.object_id=$2::uuid
                   ORDER BY t.name""",
                object_type,
                parent_id,
            )
            items = [
                {
                    "id": str(r["id"]),
                    "href": f"/ovirt-engine/api/tags/{r['id']}",
                    "name": r["name"],
                    "description": r["description"] or "",
                }
                for r in rows
            ]
            return respond(request, element="tag", collection="tags", data=items)
        if len(rest) == 1:
            r = await conn.fetchrow(
                """SELECT t.*
                   FROM ov_tag_assignments a
                   JOIN ov_tags t ON t.id = a.tag_id
                   WHERE a.object_type=$1 AND a.object_id=$2::uuid AND t.id=$3::uuid""",
                object_type,
                parent_id,
                rest[0],
            )
            if r is None:
                raise OVirtError("NotFound", "tag not found", status_code=404)
            return respond(
                request,
                element="tag",
                data={
                    "id": str(r["id"]),
                    "href": f"/ovirt-engine/api/tags/{r['id']}",
                    "name": r["name"],
                    "description": r["description"] or "",
                },
            )
    if not rest:
        if method == "GET":
            rows = await conn.fetch(
                """SELECT * FROM ov_api_objects
                   WHERE collection=$1 AND parent_collection=$2 AND parent_id=$3::uuid
                   ORDER BY name""",
                collection_key,
                parent_collection,
                parent_id,
            )
            items = [
                generic_entity(f"{parent_collection}/{parent_id}/{sub}", element, r) for r in rows
            ]
            # Fix hrefs
            for item, row in zip(items, rows, strict=False):
                item["href"] = f"/ovirt-engine/api/{parent_collection}/{parent_id}/{sub}/{row['id']}"
            return respond(request, element=element, collection=sub, data=items)
        if method == "POST":
            body = unwrap_entity(payload, element)
            oid = uuid4()
            name = str(body.get("name") or f"{element}-{oid.hex[:8]}")
            await conn.execute(
                """INSERT INTO ov_api_objects(id, collection, name, status, parent_collection, parent_id, data)
                   VALUES($1,$2,$3,$4,$5,$6::uuid,$7::jsonb)""",
                oid,
                collection_key,
                name,
                str(body.get("status") or default_status),
                parent_collection,
                parent_id,
                json.dumps(body),
            )
            row = await conn.fetchrow("SELECT * FROM ov_api_objects WHERE id=$1", oid)
            data = generic_entity(f"{parent_collection}/{parent_id}/{sub}", element, row)
            data["href"] = f"/ovirt-engine/api/{parent_collection}/{parent_id}/{sub}/{oid}"
            return respond(request, element=element, data=data, status_code=201)
    if len(rest) == 1:
        oid = rest[0]
        if method == "GET":
            row = await conn.fetchrow(
                """SELECT * FROM ov_api_objects WHERE id=$1::uuid AND collection=$2
                   AND parent_id=$3::uuid""",
                oid,
                collection_key,
                parent_id,
            )
            if row is None:
                from app.ovirt.common import no_such

                raise no_such(element, oid)
            data = generic_entity(sub, element, row, entity_id=oid)
            data["href"] = f"/ovirt-engine/api/{parent_collection}/{parent_id}/{sub}/{oid}"
            return respond(request, element=element, data=data)
        if method == "DELETE":
            await conn.execute(
                "DELETE FROM ov_api_objects WHERE id=$1::uuid AND parent_id=$2::uuid",
                oid,
                parent_id,
            )
            return Response(status_code=200)
        if method == "PUT":
            body = unwrap_entity(payload, element)
            await conn.execute(
                "UPDATE ov_api_objects SET data=$2::jsonb, updated_at=now() WHERE id=$1::uuid",
                oid,
                json.dumps(body),
            )
            row = await conn.fetchrow("SELECT * FROM ov_api_objects WHERE id=$1::uuid", oid)
            return respond(request, element=element, data=generic_entity(sub, element, row))
    if len(rest) == 2 and method == "POST":
        from app.ovirt.jobs import respond_action

        return await respond_action(
            request, conn, description=f"{parent_collection}/{sub} {rest[1]}"
        )
    raise OVirtError(
        "NotFound",
        f"No handler for /{parent_collection}/{parent_id}/{sub}/{'/'.join(rest)}",
        status_code=404,
    )


def remount_schema_services(app: Any, series: str) -> int:
    """Hot-swap contract pack: reload ops and re-register OpenAPI routes."""

    from app.ovirt.contract_loader import ensure_loaded
    from app.ovirt.registry import clear_ovirt_contract_routes, register_ovirt_contract_routes
    from app.ovirt.routes import engine

    rt = ensure_loaded(series)
    summary = rt.reload(series)
    clear_ovirt_contract_routes(app)
    registered = 0
    if rt.pack is not None:
        registered = register_ovirt_contract_routes(app, rt.pack)
    # Re-attach catch-all after specific contract routes (match order matters).
    app.include_router(engine.router)
    app.state.ovirt_series = series
    app.state.ovirt_schema_ops = registered or summary.get("operation_count", 0)
    app.state.runtime_version = f"ovirt-{series}"
    return int(app.state.ovirt_schema_ops)
