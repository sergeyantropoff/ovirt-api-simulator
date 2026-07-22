"""Shared oVirt Engine helpers (existence checks, native NotFound faults)."""

from __future__ import annotations

from typing import Any

from asyncpg import Connection

from app.ovirt.errors import OVirtError


def no_such(kind: str, entity_id: str) -> OVirtError:
    """Engine-shaped 404 with the bad id in the detail (never an HTML page)."""

    return OVirtError(
        "NotFound",
        f"No such {kind} ('{entity_id}')",
        status_code=404,
    )


async def require_host(conn: Connection, host_id: str) -> Any:
    row = await conn.fetchrow("SELECT * FROM ov_hosts WHERE id=$1::uuid", host_id)
    if row is None:
        raise no_such("host", host_id)
    return row


async def require_datacenter(conn: Connection, datacenter_id: str) -> Any:
    row = await conn.fetchrow(
        "SELECT * FROM ov_datacenters WHERE id=$1::uuid",
        datacenter_id,
    )
    if row is None:
        raise no_such("datacenter", datacenter_id)
    return row


async def require_cluster(conn: Connection, cluster_id: str) -> Any:
    row = await conn.fetchrow("SELECT * FROM ov_clusters WHERE id=$1::uuid", cluster_id)
    if row is None:
        raise no_such("cluster", cluster_id)
    return row
