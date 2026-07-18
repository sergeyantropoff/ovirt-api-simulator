"""Map database rows to oVirt Engine API entities."""

from __future__ import annotations

import json
from typing import Any


def _data(row: Any) -> dict[str, Any]:
    raw = row["data"] if "data" in row.keys() else {}
    if isinstance(raw, str):
        raw = json.loads(raw)
    return dict(raw or {})


def href(collection: str, object_id: Any) -> str:
    return f"/ovirt-engine/api/{collection}/{object_id}"


def link(rel: str, path: str) -> dict[str, str]:
    return {"@rel": rel, "href": path} if False else {"rel": rel, "href": path}


def vm_entity(row: Any) -> dict[str, Any]:
    vid = str(row["id"])
    entity = {
        "id": vid,
        "href": href("vms", vid),
        "name": row["name"],
        "description": row["description"] or "",
        "status": row["status"],
        "type": row["type"],
        "memory": int(row["memory"]),
        "cpu": {
            "topology": {
                "sockets": int(row["cpu_sockets"]),
                "cores": int(row["cpu_cores"]),
                "threads": int(row["cpu_threads"]),
            }
        },
        "os": {"type": row["os_type"]},
        "cluster": {"id": str(row["cluster_id"]), "href": href("clusters", row["cluster_id"])},
        "link": [
            {"rel": "diskattachments", "href": f"/ovirt-engine/api/vms/{vid}/diskattachments"},
            {"rel": "nics", "href": f"/ovirt-engine/api/vms/{vid}/nics"},
            {"rel": "snapshots", "href": f"/ovirt-engine/api/vms/{vid}/snapshots"},
            {"rel": "tags", "href": f"/ovirt-engine/api/vms/{vid}/tags"},
            {"rel": "permissions", "href": f"/ovirt-engine/api/vms/{vid}/permissions"},
            {"rel": "cdroms", "href": f"/ovirt-engine/api/vms/{vid}/cdroms"},
            {"rel": "graphicsconsoles", "href": f"/ovirt-engine/api/vms/{vid}/graphicsconsoles"},
        ],
    }
    if row["template_id"]:
        entity["template"] = {
            "id": str(row["template_id"]),
            "href": href("templates", row["template_id"]),
        }
    if row["host_id"]:
        entity["host"] = {"id": str(row["host_id"]), "href": href("hosts", row["host_id"])}
    entity.update({k: v for k, v in _data(row).items() if k not in entity})
    return entity


def disk_entity(row: Any) -> dict[str, Any]:
    did = str(row["id"])
    entity = {
        "id": did,
        "href": href("disks", did),
        "name": row["name"],
        "description": row["description"] or "",
        "status": row["status"],
        "provisioned_size": int(row["provisioned_size"]),
        "actual_size": int(row["actual_size"]),
        "format": row["format"],
        "sparse": bool(row["sparse"]),
        "shareable": bool(row["shareable"]),
        "wipe_after_delete": bool(row["wipe_after_delete"]),
        "link": [
            {"rel": "permissions", "href": f"/ovirt-engine/api/disks/{did}/permissions"},
            {"rel": "statistics", "href": f"/ovirt-engine/api/disks/{did}/statistics"},
        ],
    }
    if row["storage_domain_id"]:
        entity["storage_domains"] = {
            "storage_domain": [
                {
                    "id": str(row["storage_domain_id"]),
                    "href": href("storagedomains", row["storage_domain_id"]),
                }
            ]
        }
    entity.update({k: v for k, v in _data(row).items() if k not in entity})
    return entity


def host_entity(row: Any) -> dict[str, Any]:
    hid = str(row["id"])
    return {
        "id": hid,
        "href": href("hosts", hid),
        "name": row["name"],
        "address": row["address"],
        "status": row["status"],
        "type": row["type"],
        "memory": int(row["memory"]),
        "cpu": {"topology": {"cores": int(row["cpu_cores"])}},
        "cluster": {"id": str(row["cluster_id"]), "href": href("clusters", row["cluster_id"])},
        "link": [
            {"rel": "nics", "href": f"/ovirt-engine/api/hosts/{hid}/nics"},
            {"rel": "tags", "href": f"/ovirt-engine/api/hosts/{hid}/tags"},
            {"rel": "permissions", "href": f"/ovirt-engine/api/hosts/{hid}/permissions"},
            {"rel": "statistics", "href": f"/ovirt-engine/api/hosts/{hid}/statistics"},
        ],
        **{k: v for k, v in _data(row).items()},
    }


def datacenter_entity(row: Any) -> dict[str, Any]:
    did = str(row["id"])
    return {
        "id": did,
        "href": href("datacenters", did),
        "name": row["name"],
        "description": row["description"] or "",
        "local": bool(row["local"]),
        "status": row["status"],
        "version": {"major": int(row["version_major"]), "minor": int(row["version_minor"])},
        "link": [
            {"rel": "clusters", "href": f"/ovirt-engine/api/datacenters/{did}/clusters"},
            {"rel": "storagedomains", "href": f"/ovirt-engine/api/datacenters/{did}/storagedomains"},
            {"rel": "networks", "href": f"/ovirt-engine/api/datacenters/{did}/networks"},
            {"rel": "quotas", "href": f"/ovirt-engine/api/datacenters/{did}/quotas"},
            {"rel": "permissions", "href": f"/ovirt-engine/api/datacenters/{did}/permissions"},
        ],
        **{k: v for k, v in _data(row).items()},
    }


def cluster_entity(row: Any) -> dict[str, Any]:
    cid = str(row["id"])
    return {
        "id": cid,
        "href": href("clusters", cid),
        "name": row["name"],
        "description": row["description"] or "",
        "cpu": {"type": row["cpu_type"]},
        "version": {"major": int(row["version_major"]), "minor": int(row["version_minor"])},
        "data_center": {
            "id": str(row["datacenter_id"]),
            "href": href("datacenters", row["datacenter_id"]),
        },
        "link": [
            {"rel": "networks", "href": f"/ovirt-engine/api/clusters/{cid}/networks"},
            {"rel": "affinitygroups", "href": f"/ovirt-engine/api/clusters/{cid}/affinitygroups"},
            {"rel": "permissions", "href": f"/ovirt-engine/api/clusters/{cid}/permissions"},
        ],
        **{k: v for k, v in _data(row).items()},
    }


def network_entity(row: Any) -> dict[str, Any]:
    nid = str(row["id"])
    entity: dict[str, Any] = {
        "id": nid,
        "href": href("networks", nid),
        "name": row["name"],
        "description": row["description"] or "",
        "stp": bool(row["stp"]),
        "data_center": {
            "id": str(row["datacenter_id"]),
            "href": href("datacenters", row["datacenter_id"]),
        },
        "link": [
            {"rel": "vnicprofiles", "href": f"/ovirt-engine/api/networks/{nid}/vnicprofiles"},
            {"rel": "permissions", "href": f"/ovirt-engine/api/networks/{nid}/permissions"},
        ],
    }
    if row["vlan_id"] is not None:
        entity["vlan"] = {"id": int(row["vlan_id"])}
    entity.update(_data(row))
    return entity


def storage_domain_entity(row: Any) -> dict[str, Any]:
    sid = str(row["id"])
    return {
        "id": sid,
        "href": href("storagedomains", sid),
        "name": row["name"],
        "type": row["type"],
        "storage": {"type": row["storage_type"]},
        "status": row["status"],
        "available": int(row["available"]),
        "used": int(row["used"]),
        "committed": int(row["committed"]),
        "link": [
            {"rel": "disks", "href": f"/ovirt-engine/api/storagedomains/{sid}/disks"},
            {"rel": "files", "href": f"/ovirt-engine/api/storagedomains/{sid}/files"},
            {"rel": "permissions", "href": f"/ovirt-engine/api/storagedomains/{sid}/permissions"},
        ],
        **{k: v for k, v in _data(row).items()},
    }


def template_entity(row: Any) -> dict[str, Any]:
    tid = str(row["id"])
    entity: dict[str, Any] = {
        "id": tid,
        "href": href("templates", tid),
        "name": row["name"],
        "description": row["description"] or "",
        "status": row["status"],
        "memory": int(row["memory"]),
        "cpu": {
            "topology": {"sockets": int(row["cpu_sockets"]), "cores": int(row["cpu_cores"])}
        },
        "link": [
            {"rel": "diskattachments", "href": f"/ovirt-engine/api/templates/{tid}/diskattachments"},
            {"rel": "nics", "href": f"/ovirt-engine/api/templates/{tid}/nics"},
        ],
    }
    if row["cluster_id"]:
        entity["cluster"] = {
            "id": str(row["cluster_id"]),
            "href": href("clusters", row["cluster_id"]),
        }
    entity.update(_data(row))
    return entity


def user_entity(row: Any) -> dict[str, Any]:
    uid = str(row["id"])
    return {
        "id": uid,
        "href": href("users", uid),
        "name": row["name"],
        "user_name": f"{row['name']}@{row['domain_name']}",
        "domain": {"id": str(row["domain_id"]), "name": row["domain_name"]},
        "link": [
            {"rel": "roles", "href": f"/ovirt-engine/api/users/{uid}/roles"},
            {"rel": "permissions", "href": f"/ovirt-engine/api/users/{uid}/permissions"},
            {"rel": "tags", "href": f"/ovirt-engine/api/users/{uid}/tags"},
        ],
    }


def generic_entity(collection: str, element: str, row: Any) -> dict[str, Any]:
    if row is None:
        from app.ovirt.errors import OVirtError

        raise OVirtError("NotFound", f"{element} not found", status_code=404)
    oid = str(row["id"])
    data = _data(row)
    entity = {
        "id": oid,
        "href": href(collection, oid),
        "name": row["name"] or data.get("name") or element,
        "status": row["status"],
    }
    entity.update(data)
    return entity


def job_entity(row: Any) -> dict[str, Any]:
    jid = str(row["id"])
    entity: dict[str, Any] = {
        "id": jid,
        "href": href("jobs", jid),
        "description": row["description"] or "",
        "status": row["status"],
    }
    if row["started"] is not None:
        entity["started"] = row["started"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if row["ended"] is not None:
        entity["ended"] = row["ended"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    entity.update({k: v for k, v in _data(row).items() if k not in entity and k != "action_status"})
    return entity


def action_entity(job_row: Any) -> dict[str, Any]:
    """Build an action response from a persisted job row (status from job.data)."""

    data = _data(job_row)
    status = data.get("action_status")
    if status is None:
        status = job_row["status"]
    return {"status": str(status), "job": job_entity(job_row)}


def disk_attachment_entity(row: Any, *, vm_id: str | None = None) -> dict[str, Any]:
    vid = vm_id or str(row["vm_id"])
    aid = str(row["id"])
    entity: dict[str, Any] = {
        "id": aid,
        "href": f"/ovirt-engine/api/vms/{vid}/diskattachments/{aid}",
        "active": bool(row["active"]),
        "bootable": bool(row["bootable"]),
        "interface": row["interface"],
        "disk": {"id": str(row["disk_id"]), "href": href("disks", row["disk_id"])},
        "vm": {"id": vid, "href": href("vms", vid)},
    }
    if "disk_name" in row.keys() and row["disk_name"] is not None:
        entity["disk"]["name"] = row["disk_name"]
    entity.update({k: v for k, v in _data(row).items() if k not in entity})
    return entity


def nic_entity(row: Any, *, vm_id: str | None = None) -> dict[str, Any]:
    vid = vm_id or str(row["vm_id"])
    nid = str(row["id"])
    entity: dict[str, Any] = {
        "id": nid,
        "href": f"/ovirt-engine/api/vms/{vid}/nics/{nid}",
        "name": row["name"],
        "interface": row["interface"],
        "linked": bool(row["linked"]),
        "plugged": bool(row["plugged"]),
        "mac": {"address": row["mac_address"] or ""},
    }
    if row["vnic_profile_id"]:
        entity["vnic_profile"] = {
            "id": str(row["vnic_profile_id"]),
            "href": href("vnicprofiles", row["vnic_profile_id"]),
        }
    entity.update({k: v for k, v in _data(row).items() if k not in entity})
    return entity


def snapshot_entity(row: Any, *, vm_id: str | None = None) -> dict[str, Any]:
    vid = vm_id or str(row["vm_id"])
    sid = str(row["id"])
    entity: dict[str, Any] = {
        "id": sid,
        "href": f"/ovirt-engine/api/vms/{vid}/snapshots/{sid}",
        "description": row["description"] or "",
        "status": row["status"],
        "snapshot_type": row["snapshot_type"],
        "persist_memorystate": bool(row["persist_memorystate"]),
    }
    if row["created_at"] is not None:
        entity["date"] = row["created_at"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    entity.update({k: v for k, v in _data(row).items() if k not in entity})
    return entity


def tag_entity(row: Any) -> dict[str, Any]:
    tid = str(row["id"])
    return {
        "id": tid,
        "href": href("tags", tid),
        "name": row["name"],
        "description": row["description"] or "",
    }
