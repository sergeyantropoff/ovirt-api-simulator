"""Engine runtime settings stored in `ov_api_objects` (collection=options)."""

from __future__ import annotations

import json
from typing import Any

from asyncpg import Connection

from app.ovirt.ids import stable_id

# Seeded option names (values live only in Postgres).
OPT_DEFAULT_VM_MEMORY = "DEFAULT_VM_MEMORY"
OPT_DEFAULT_DISK_SIZE = "DEFAULT_DISK_SIZE"
OPT_DEFAULT_HOST_MEMORY = "DEFAULT_HOST_MEMORY"
OPT_DEFAULT_HOST_CPU_CORES = "DEFAULT_HOST_CPU_CORES"
OPT_DEFAULT_CPU_SOCKETS = "DEFAULT_CPU_SOCKETS"
OPT_DEFAULT_CPU_CORES = "DEFAULT_CPU_CORES"
OPT_DEFAULT_CPU_THREADS = "DEFAULT_CPU_THREADS"
OPT_DEFAULT_NIC_INTERFACE = "DEFAULT_NIC_INTERFACE"
OPT_DEFAULT_DISK_INTERFACE = "DEFAULT_DISK_INTERFACE"
OPT_DEFAULT_DISK_FORMAT = "DEFAULT_DISK_FORMAT"
OPT_DEFAULT_VM_TYPE = "DEFAULT_VM_TYPE"
OPT_DEFAULT_OS_TYPE = "DEFAULT_OS_TYPE"
OPT_DEFAULT_VM_STATUS = "DEFAULT_VM_STATUS"
OPT_DEFAULT_HOST_STATUS = "DEFAULT_HOST_STATUS"
OPT_DEFAULT_DC_STATUS = "DEFAULT_DC_STATUS"
OPT_DEFAULT_SD_STATUS = "DEFAULT_SD_STATUS"
OPT_DEFAULT_HOST_ADDRESS = "DEFAULT_HOST_ADDRESS"
OPT_DEFAULT_CLUSTER_CPU_TYPE = "DEFAULT_CLUSTER_CPU_TYPE"
OPT_DEFAULT_SD_TYPE = "DEFAULT_SD_TYPE"
OPT_DEFAULT_STORAGE_TYPE = "DEFAULT_STORAGE_TYPE"
OPT_DEFAULT_SD_AVAILABLE = "DEFAULT_SD_AVAILABLE"
OPT_DEFAULT_STORAGE_CONNECTION_TYPE = "DEFAULT_STORAGE_CONNECTION_TYPE"
OPT_DEFAULT_MAC_PREFIX = "DEFAULT_MAC_PREFIX"
OPT_DEFAULT_NIC_NAME = "DEFAULT_NIC_NAME"
OPT_DEFAULT_SNAPSHOT_DESCRIPTION = "DEFAULT_SNAPSHOT_DESCRIPTION"
OPT_DEFAULT_TAG_NAME = "DEFAULT_TAG_NAME"
OPT_DEFAULT_API_OBJECT_STATUS = "DEFAULT_API_OBJECT_STATUS"
OPT_DEFAULT_ACTION_STATUS = "DEFAULT_ACTION_STATUS"
OPT_DEFAULT_JOB_STATUS_COMPLETE = "DEFAULT_JOB_STATUS_COMPLETE"
OPT_DEFAULT_JOB_STATUS_STARTED = "DEFAULT_JOB_STATUS_STARTED"
OPT_DEFAULT_JOB_STEP_TYPE = "DEFAULT_JOB_STEP_TYPE"
OPT_DEFAULT_AUTH_DOMAIN = "DEFAULT_AUTH_DOMAIN"
OPT_DEFAULT_API_SCOPE = "DEFAULT_API_SCOPE"
OPT_DEFAULT_TOKEN_TYPE = "DEFAULT_TOKEN_TYPE"
OPT_DEFAULT_USER_ROLE = "DEFAULT_USER_ROLE"
OPT_OAUTH_TOKEN_TTL_SECONDS = "OAUTH_TOKEN_TTL_SECONDS"
OPT_BASIC_SESSION_TTL_SECONDS = "BASIC_SESSION_TTL_SECONDS"
OPT_SD_ATTACH_ACTIVE = "SD_ATTACH_STATUS_ACTIVE"
OPT_SD_ATTACH_MAINTENANCE = "SD_ATTACH_STATUS_MAINTENANCE"
OPT_PRODUCT_NAME = "PRODUCT_NAME"
OPT_PRODUCT_VENDOR = "PRODUCT_VENDOR"
OPT_PRODUCT_MAJOR = "PRODUCT_MAJOR"
OPT_PRODUCT_MINOR = "PRODUCT_MINOR"
OPT_PRODUCT_BUILD = "PRODUCT_BUILD"
OPT_PRODUCT_REVISION = "PRODUCT_REVISION"
OPT_PRODUCT_FULL = "PRODUCT_FULL"
OPT_ENGINE_API_DEFAULT_VERSION = "ENGINE_API_DEFAULT_VERSION"
OPT_VM_ACTION_STATUS_MAP = "VM_ACTION_STATUS_MAP"
OPT_HOST_ACTION_STATUS_MAP = "HOST_ACTION_STATUS_MAP"

_VM_ACTION_MAP = {
    "start": "up",
    "stop": "down",
    "shutdown": "down",
    "reboot": "up",
    "suspend": "suspended",
    "migrate": "up",
    "cancelmigration": "up",
    "maintenance": "down",
    "logon": "up",
    "freeze_filesystems": "up",
    "thaw_filesystems": "up",
}

_HOST_ACTION_MAP = {
    "activate": "up",
    "deactivate": "maintenance",
    "approve": "up",
    "install": "up",
    "fence": "down",
    "refresh": "up",
    "upgrade": "up",
    "upgradecheck": "up",
    "commitnetconfig": "up",
    "enrollcertificate": "up",
    "iscsidiscover": "up",
    "iscsilogin": "up",
    "unregisteredstoragedomainsdiscover": "up",
}

_DEFAULT_OPTIONS: list[tuple[str, str]] = [
    (OPT_DEFAULT_VM_MEMORY, str(1024**3)),
    (OPT_DEFAULT_DISK_SIZE, str(10 * 1024**3)),
    (OPT_DEFAULT_HOST_MEMORY, str(64 * 1024**3)),
    (OPT_DEFAULT_HOST_CPU_CORES, "16"),
    (OPT_DEFAULT_CPU_SOCKETS, "1"),
    (OPT_DEFAULT_CPU_CORES, "1"),
    (OPT_DEFAULT_CPU_THREADS, "1"),
    (OPT_DEFAULT_NIC_INTERFACE, "virtio"),
    (OPT_DEFAULT_DISK_INTERFACE, "virtio_scsi"),
    (OPT_DEFAULT_DISK_FORMAT, "cow"),
    (OPT_DEFAULT_VM_TYPE, "server"),
    (OPT_DEFAULT_OS_TYPE, "other"),
    (OPT_DEFAULT_VM_STATUS, "down"),
    (OPT_DEFAULT_HOST_STATUS, "up"),
    (OPT_DEFAULT_DC_STATUS, "up"),
    (OPT_DEFAULT_SD_STATUS, "active"),
    (OPT_DEFAULT_HOST_ADDRESS, "127.0.0.1"),
    (OPT_DEFAULT_CLUSTER_CPU_TYPE, "Intel Conroe Family"),
    (OPT_DEFAULT_SD_TYPE, "data"),
    (OPT_DEFAULT_STORAGE_TYPE, "nfs"),
    (OPT_DEFAULT_SD_AVAILABLE, str(1024**4)),
    (OPT_DEFAULT_STORAGE_CONNECTION_TYPE, "nfs"),
    (OPT_DEFAULT_MAC_PREFIX, "00:1a:4a"),
    (OPT_DEFAULT_NIC_NAME, "nic1"),
    (OPT_DEFAULT_SNAPSHOT_DESCRIPTION, "snapshot"),
    (OPT_DEFAULT_TAG_NAME, "tag"),
    (OPT_DEFAULT_API_OBJECT_STATUS, "ok"),
    (OPT_DEFAULT_ACTION_STATUS, "complete"),
    (OPT_DEFAULT_JOB_STATUS_COMPLETE, "finished"),
    (OPT_DEFAULT_JOB_STATUS_STARTED, "started"),
    (OPT_DEFAULT_JOB_STEP_TYPE, "executing"),
    (OPT_DEFAULT_AUTH_DOMAIN, "internal"),
    (OPT_DEFAULT_API_SCOPE, "ovirt-app-api"),
    (OPT_DEFAULT_TOKEN_TYPE, "bearer"),
    (OPT_DEFAULT_USER_ROLE, "UserRole"),
    (OPT_OAUTH_TOKEN_TTL_SECONDS, "3600"),
    (OPT_BASIC_SESSION_TTL_SECONDS, "7200"),
    (OPT_SD_ATTACH_ACTIVE, "active"),
    (OPT_SD_ATTACH_MAINTENANCE, "maintenance"),
    (OPT_PRODUCT_NAME, "oVirt Engine"),
    (OPT_PRODUCT_VENDOR, "ovirt.org"),
    (OPT_PRODUCT_MAJOR, "4"),
    (OPT_PRODUCT_MINOR, "5"),
    (OPT_PRODUCT_BUILD, "0"),
    (OPT_PRODUCT_REVISION, "0"),
    (OPT_PRODUCT_FULL, "4.5.0"),
    (OPT_ENGINE_API_DEFAULT_VERSION, "4"),
    (OPT_VM_ACTION_STATUS_MAP, json.dumps(_VM_ACTION_MAP, separators=(",", ":"))),
    (OPT_HOST_ACTION_STATUS_MAP, json.dumps(_HOST_ACTION_MAP, separators=(",", ":"))),
]


async def seed_engine_options(conn: Connection) -> None:
    """Upsert Engine options used by handlers (create defaults + product_info)."""

    for name, value in _DEFAULT_OPTIONS:
        await conn.execute(
            """INSERT INTO ov_api_objects(id, collection, name, status, data)
               VALUES($1,'options',$2,'ok',$3::jsonb)
               ON CONFLICT (id) DO UPDATE SET
                 data=EXCLUDED.data, name=EXCLUDED.name, status='ok', updated_at=now()""",
            stable_id("obj", "options", name),
            name,
            json.dumps({"name": name, "value": value, "description": f"engine option {name}"}),
        )


async def option_value(conn: Connection, name: str) -> str:
    row = await conn.fetchrow(
        """SELECT data FROM ov_api_objects
           WHERE collection='options' AND name=$1""",
        name,
    )
    if row is None:
        raise RuntimeError(f"missing engine option in DB: {name} (reload seed)")
    data = row["data"]
    if isinstance(data, str):
        data = json.loads(data)
    data = dict(data or {})
    if "value" in data and data["value"] is not None:
        return str(data["value"])
    raise RuntimeError(f"engine option {name} has no value in DB")


async def option_int(conn: Connection, name: str) -> int:
    return int(await option_value(conn, name))


async def option_json(conn: Connection, name: str) -> Any:
    raw = await option_value(conn, name)
    return json.loads(raw)


async def product_info_from_db(conn: Connection) -> dict[str, Any]:
    return {
        "name": await option_value(conn, OPT_PRODUCT_NAME),
        "vendor": await option_value(conn, OPT_PRODUCT_VENDOR),
        "version": {
            "major": await option_value(conn, OPT_PRODUCT_MAJOR),
            "minor": await option_value(conn, OPT_PRODUCT_MINOR),
            "build": await option_value(conn, OPT_PRODUCT_BUILD),
            "revision": await option_value(conn, OPT_PRODUCT_REVISION),
            "full_version": await option_value(conn, OPT_PRODUCT_FULL),
        },
    }
