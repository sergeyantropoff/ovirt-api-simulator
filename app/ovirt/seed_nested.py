"""Seed nested Engine subcollections so entity `link` hrefs are non-empty.

Rows go into `ov_api_objects` (with parent_collection/parent_id) and into
`ov_permissions` / `ov_tag_assignments` where specialized tables exist.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from asyncpg import Connection

from app.ovirt.ids import stable_id


def _obj_row(
    *,
    parent_collection: str,
    parent_id: UUID,
    collection: str,
    name: str,
    data: dict[str, Any] | None = None,
    status: str = "ok",
) -> tuple[Any, ...]:
    payload = {"name": name, **(data or {})}
    return (
        stable_id("nested", parent_collection, str(parent_id), collection, name),
        collection,
        name,
        status,
        parent_collection,
        parent_id,
        json.dumps(payload),
    )


async def _insert_objs(conn: Connection, rows: list[tuple[Any, ...]]) -> None:
    if not rows:
        return
    await conn.executemany(
        """INSERT INTO ov_api_objects(
               id, collection, name, status, parent_collection, parent_id, data
           ) VALUES($1,$2,$3,$4,$5,$6::uuid,$7::jsonb)
           ON CONFLICT (id) DO NOTHING""",
        rows,
    )


async def seed_nested_for_inventory(
    conn: Connection,
    *,
    admin_user_id: UUID,
    role_user_id: UUID,
    datacenter_ids: list[UUID],
    cluster_ids: list[UUID],
    host_ids: list[UUID],
    network_ids: list[UUID],
    storage_domain_ids: list[UUID],
    template_ids: list[UUID],
    vm_ids: list[UUID],
    disk_ids: list[UUID],
    tag_ids: list[UUID] | None = None,
    user_ids: list[UUID] | None = None,
    group_ids: list[UUID] | None = None,
) -> None:
    """Populate nested surface for the given inventory sample."""

    obj_rows: list[tuple[Any, ...]] = []
    perm_rows: list[tuple[Any, ...]] = []
    tag_rows: list[tuple[Any, ...]] = []
    if user_ids is None:
        user_ids = []
    if group_ids is None:
        group_ids = []

    def perm(object_type: str, object_id: UUID, key: str) -> None:
        perm_rows.append(
            (
                stable_id("perm", object_type, key),
                role_user_id,
                admin_user_id,
                object_type,
                object_id,
            )
        )

    for dc_id in datacenter_ids:
        perm("data_center", dc_id, f"dc-{dc_id}")
        obj_rows.append(
            _obj_row(
                parent_collection="datacenters",
                parent_id=dc_id,
                collection="qoss",
                name="default-qos",
                data={"type": "storage"},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="datacenters",
                parent_id=dc_id,
                collection="iscsibonds",
                name="iscsi-bond-1",
                data={"description": "iSCSI bond"},
            )
        )

    for cluster_id in cluster_ids:
        perm("cluster", cluster_id, f"cluster-{cluster_id}")
        obj_rows.append(
            _obj_row(
                parent_collection="clusters",
                parent_id=cluster_id,
                collection="cpuprofiles",
                name="Default",
                data={"description": "Default CPU profile"},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="clusters",
                parent_id=cluster_id,
                collection="enabledfeatures",
                name="gluster",
                data={"description": "Gluster feature"},
            )
        )

    for host_id in host_ids:
        perm("host", host_id, f"host-{host_id}")
        obj_rows.append(
            _obj_row(
                parent_collection="hosts",
                parent_id=host_id,
                collection="nics",
                name="eth0",
                data={"mac": {"address": "00:1a:4a:00:00:01"}, "boot_protocol": "dhcp"},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="hosts",
                parent_id=host_id,
                collection="nics",
                name="eth1",
                data={"mac": {"address": "00:1a:4a:00:00:02"}, "boot_protocol": "none"},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="hosts",
                parent_id=host_id,
                collection="statistics",
                name="memory.used",
                data={"unit": "bytes", "values": {"value": [{"datum": 8 * 1024**3}]}},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="hosts",
                parent_id=host_id,
                collection="statistics",
                name="cpu.current.user",
                data={"unit": "percent", "values": {"value": [{"datum": 12.5}]}},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="hosts",
                parent_id=host_id,
                collection="devices",
                name="pci-0000:00:1f.2",
                data={"capability": "storage", "vendor": "lab"},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="hosts",
                parent_id=host_id,
                collection="hooks",
                name="before_vm_start",
                data={"event_name": "before_vm_start"},
            )
        )
        if tag_ids:
            tag_rows.append(
                (
                    stable_id("ta", "host", str(host_id), str(tag_ids[0])),
                    tag_ids[0],
                    "host",
                    host_id,
                )
            )

    for net_id in network_ids:
        perm("network", net_id, f"net-{net_id}")

    for sd_id in storage_domain_ids:
        perm("storage_domain", sd_id, f"sd-{sd_id}")
        obj_rows.append(
            _obj_row(
                parent_collection="storagedomains",
                parent_id=sd_id,
                collection="files",
                name="rhel-9.iso",
                data={"type": "iso", "size": 8 * 1024**3},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="storagedomains",
                parent_id=sd_id,
                collection="files",
                name="virtio-win.iso",
                data={"type": "iso", "size": 512 * 1024**2},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="storagedomains",
                parent_id=sd_id,
                collection="images",
                name="base-image",
                data={"description": "Base disk image"},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="storagedomains",
                parent_id=sd_id,
                collection="diskprofiles",
                name="default",
                data={"description": "Default disk profile"},
            )
        )

    for tpl_id in template_ids:
        perm("template", tpl_id, f"tpl-{tpl_id}")
        obj_rows.append(
            _obj_row(
                parent_collection="templates",
                parent_id=tpl_id,
                collection="nics",
                name="nic1",
                data={"interface": "virtio"},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="templates",
                parent_id=tpl_id,
                collection="diskattachments",
                name="disk1",
                data={"bootable": True, "interface": "virtio_scsi"},
            )
        )
        obj_rows.append(
            _obj_row(
                parent_collection="templates",
                parent_id=tpl_id,
                collection="cdroms",
                name="ide0",
                data={"file": {"id": "rhel-9.iso"}},
            )
        )

    for disk_id in disk_ids:
        perm("disk", disk_id, f"disk-{disk_id}")
        obj_rows.append(
            _obj_row(
                parent_collection="disks",
                parent_id=disk_id,
                collection="statistics",
                name="data.current.read",
                data={"unit": "bytespers", "values": {"value": [{"datum": 1024}]}},
            )
        )

    if tag_ids:
        for user_id in user_ids:
            tag_rows.append(
                (
                    stable_id("ta", "user", str(user_id), str(tag_ids[0])),
                    tag_ids[0],
                    "user",
                    user_id,
                )
            )
        for group_id in group_ids:
            perm("group", group_id, f"group-{group_id}")
            tag_rows.append(
                (
                    stable_id("ta", "group", str(group_id), str(tag_ids[0])),
                    tag_ids[0],
                    "group",
                    group_id,
                )
            )
    else:
        for group_id in group_ids:
            perm("group", group_id, f"group-{group_id}")

    for vm_id in vm_ids:
        perm("vm", vm_id, f"vm-{vm_id}")
        obj_rows.extend(
            [
                _obj_row(
                    parent_collection="vms",
                    parent_id=vm_id,
                    collection="cdroms",
                    name="ide0",
                    data={"file": {"id": "rhel-9.iso"}},
                ),
                _obj_row(
                    parent_collection="vms",
                    parent_id=vm_id,
                    collection="graphicsconsoles",
                    name="vnc",
                    data={"protocol": "vnc", "port": 5900, "address": "127.0.0.1"},
                ),
                _obj_row(
                    parent_collection="vms",
                    parent_id=vm_id,
                    collection="graphicsconsoles",
                    name="spice",
                    data={"protocol": "spice", "port": 5901},
                ),
                _obj_row(
                    parent_collection="vms",
                    parent_id=vm_id,
                    collection="reporteddevices",
                    name="eth0",
                    data={"type": "network", "mac": {"address": "00:1a:4a:01:00:01"}},
                ),
                _obj_row(
                    parent_collection="vms",
                    parent_id=vm_id,
                    collection="sessions",
                    name="console-1",
                    data={"user": {"name": "admin@internal"}, "ip": {"address": "10.0.0.1"}},
                ),
                _obj_row(
                    parent_collection="vms",
                    parent_id=vm_id,
                    collection="applications",
                    name="qemu-guest-agent",
                    data={"version": "8.2.0"},
                ),
                _obj_row(
                    parent_collection="vms",
                    parent_id=vm_id,
                    collection="watchdogs",
                    name="i6300esb",
                    data={"model": "i6300esb", "action": "reset"},
                ),
                _obj_row(
                    parent_collection="vms",
                    parent_id=vm_id,
                    collection="statistics",
                    name="memory.installed",
                    data={"unit": "bytes", "values": {"value": [{"datum": 2 * 1024**3}]}},
                ),
                _obj_row(
                    parent_collection="vms",
                    parent_id=vm_id,
                    collection="numanodes",
                    name="0",
                    data={"index": 0, "memory": 1024**3},
                ),
                _obj_row(
                    parent_collection="vms",
                    parent_id=vm_id,
                    collection="hostdevices",
                    name="pci_0000_00_02_0",
                    data={"capability": "pci"},
                ),
            ]
        )

    # Scheduling policy children + role permits
    for sp_name in ("evenly_distributed", "power_saving", "vm_evenly_distributed"):
        sp_id = await conn.fetchval(
            "SELECT id FROM ov_api_objects WHERE collection='schedulingpolicies' AND name=$1",
            sp_name,
        )
        if sp_id is None:
            continue
        for sub, child in (
            ("filters", "Memory"),
            ("weights", "EvenlyDistributed"),
            ("balances", "EvenlyDistributed"),
        ):
            obj_rows.append(
                _obj_row(
                    parent_collection="schedulingpolicies",
                    parent_id=sp_id,
                    collection=sub,
                    name=child,
                    data={"factor": 1},
                )
            )
    for role_name in ("SuperUser", "UserRole", "ClusterAdmin"):
        role_id = await conn.fetchval("SELECT id FROM ov_roles WHERE name=$1", role_name)
        if role_id is None:
            continue
        for permit in ("create_vm", "login", "manipulate_vm"):
            obj_rows.append(
                _obj_row(
                    parent_collection="roles",
                    parent_id=role_id,
                    collection="permits",
                    name=permit,
                    data={"administrative": role_name != "UserRole"},
                )
            )

    if perm_rows:
        await conn.executemany(
            """INSERT INTO ov_permissions(id, role_id, user_id, object_type, object_id)
               VALUES($1,$2,$3,$4,$5::uuid)
               ON CONFLICT (id) DO NOTHING""",
            perm_rows,
        )
    await _insert_objs(conn, obj_rows)
    if tag_rows:
        await conn.executemany(
            """INSERT INTO ov_tag_assignments(id, tag_id, object_type, object_id)
               VALUES($1,$2,$3,$4::uuid) ON CONFLICT DO NOTHING""",
            tag_rows,
        )
