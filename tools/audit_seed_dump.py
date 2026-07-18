#!/usr/bin/env python3
"""Contract-driven dump audit for minimal/demo seed against live Engine.

Probes every GET collection and entity-by-id from contracts/ovirt/<series>/api.json.
Nested `{id}` is resolved from the parent nested collection (not a global map).
Exit 0 only at 100% dump.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = sys.argv[1] if len(sys.argv) > 1 else "https://127.0.0.1:7443"
SERIES = sys.argv[2] if len(sys.argv) > 2 else "4.5"
CONTRACT = ROOT / "contracts" / "ovirt" / SERIES / "api.json"

CURL = [
    "/usr/bin/curl",
    "-sk",
    "-u",
    "admin@internal:secret",
    "-H",
    "Accept: application/json",
    "-H",
    "Version: 4",
]

PARAM_RE = re.compile(r"\{([^}]+)\}")

PLURAL_MAP = {
    "datacenter": "datacenters",
    "cluster": "clusters",
    "host": "hosts",
    "vm": "vms",
    "network": "networks",
    "storagedomain": "storagedomains",
    "template": "templates",
    "disk": "disks",
    "user": "users",
    "role": "roles",
    "job": "jobs",
    "group": "groups",
    "domain": "domains",
    "tag": "tags",
    "vnicprofile": "vnicprofiles",
    "schedulingpolicy": "schedulingpolicies",
    "bookmark": "bookmarks",
    "event": "events",
    "icon": "icons",
    "instancetype": "instancetypes",
    "macpool": "macpools",
    "networkfilter": "networkfilters",
    "operatingsystem": "operatingsystems",
    "permission": "permissions",
    "storageconnection": "storageconnections",
    "vmpool": "vmpools",
    "affinitylabel": "affinitylabels",
    "clusterlevel": "clusterlevels",
    "externalhostprovider": "externalhostproviders",
    "katelloerratum": "katelloerrata",
    "openstackimageprovider": "openstackimageproviders",
    "openstacknetworkprovider": "openstacknetworkproviders",
    "openstackvolumeprovider": "openstackvolumeproviders",
    "imagetransfer": "imagetransfers",
    "option": "options",
    "schedulingpolicyunit": "schedulingpolicyunits",
}


def get(path: str) -> tuple[int, object]:
    url = f"{ENGINE}{path}" if path.startswith("/") else f"{ENGINE}/{path}"
    out = subprocess.check_output(CURL + ["-o", "/tmp/_dump_body.json", "-w", "%{http_code}", url])
    code = int(out.decode().strip())
    raw = Path("/tmp/_dump_body.json").read_bytes()
    try:
        payload = json.loads(raw) if raw.strip() else None
    except Exception:
        payload = raw.decode(errors="replace")[:200]
    return code, payload


def items(payload: object) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    for value in payload.values():
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
        if isinstance(value, dict) and value.get("id"):
            return [value]
    return []


def first_id(payload: object) -> str | None:
    arr = items(payload)
    return arr[0].get("id") if arr else None


def skip_versioned(path: str) -> bool:
    return "/api/v4/" in path or path.rstrip("/").endswith("/api/v4")


def is_collection_get(op: dict) -> bool:
    if op.get("method") != "GET" or skip_versioned(op["path"]):
        return False
    last = op["path"].rstrip("/").split("/")[-1]
    return not last.startswith("{")


def is_entity_get(op: dict) -> bool:
    if op.get("method") != "GET" or skip_versioned(op["path"]):
        return False
    last = op["path"].rstrip("/").split("/")[-1]
    return last.startswith("{") and last.endswith("}")


def param_to_collection(param: str) -> str:
    if param.endswith("_id"):
        base = param[: -len("_id")]
        return PLURAL_MAP.get(base, base + "s")
    return PLURAL_MAP.get(param, param)


def resolve_parents(path: str, inventory: dict[str, str]) -> str | None:
    """Replace all {foo_id} parent params; leave {id} untouched."""
    out = path
    for p in PARAM_RE.findall(path):
        if p == "id":
            continue
        coll = param_to_collection(p)
        if coll not in inventory:
            return None
        out = out.replace("{" + p + "}", inventory[coll])
    return out


def resolve_entity(path: str, inventory: dict[str, str], collection_key: str | None) -> str | None:
    """Resolve entity path including nested {id} via live nested collection fetch."""
    partial = resolve_parents(path, inventory)
    if partial is None:
        return None
    if "{id}" not in partial:
        return partial
    # Nested: /…/parent/{pid}/sub/{id} → fetch …/sub for an id
    # Top-level: /…/collection/{id}
    if partial.count("/") >= 5 and not partial.rstrip("/").endswith("/{id}"):
        # shouldn't happen
        pass
    parent_coll_path = partial.rsplit("/{id}", 1)[0]
    # For top-level /api/bookmarks/{id}, parent_coll_path is the collection URL
    code, payload = get(parent_coll_path)
    if code != 200:
        return None
    fid = first_id(payload)
    if not fid:
        # top-level may need inventory by collection_key
        key = collection_key or parent_coll_path.rstrip("/").split("/")[-1]
        if key == "imageTransfers":
            key = "imagetransfers"
        fid = inventory.get(key)
    if not fid:
        return None
    return partial.replace("{id}", fid)


def good_entity(payload: object) -> bool:
    arr = items(payload)
    return len(arr) == 1 and bool(arr[0].get("id")) and bool(arr[0].get("href"))


def good_collection(payload: object) -> bool:
    arr = items(payload)
    return len(arr) >= 1 and all(i.get("id") and i.get("href") for i in arr[:5])


def main() -> int:
    ops = json.loads(CONTRACT.read_text())["operations"]
    collections = [o for o in ops if is_collection_get(o)]
    entities = [o for o in ops if is_entity_get(o)]

    inventory: dict[str, str] = {}
    for op in collections:
        if "{" in op["path"] or op["path"].rstrip("/").endswith("/api"):
            continue
        _, payload = get(op["path"])
        fid = first_id(payload)
        key = op.get("collection_key") or op["path"].rstrip("/").split("/")[-1]
        if key == "imageTransfers":
            key = "imagetransfers"
        if fid:
            inventory[key] = fid
            inventory[key.lower()] = fid

    gaps: list[str] = []
    ok = 0
    probed = 0

    for op in collections:
        template = op["path"]
        resolved = resolve_parents(template, inventory)
        probed += 1
        if resolved is None:
            gaps.append(f"UNRESOLVED {template}")
            continue
        code, payload = get(resolved)
        if template.rstrip("/").endswith("/api"):
            good = code == 200 and isinstance(payload, dict) and bool(payload)
        else:
            good = code == 200 and good_collection(payload)
        if good:
            ok += 1
        else:
            n = len(items(payload)) if isinstance(payload, dict) else 0
            gaps.append(f"GET {resolved} -> {code} count={n}")

    entity_ok = 0
    entity_probed = 0
    for op in entities:
        template = op["path"]
        entity_probed += 1
        probed += 1
        resolved = resolve_entity(template, inventory, op.get("collection_key"))
        if resolved is None:
            gaps.append(f"UNRESOLVED {template}")
            continue
        code, payload = get(resolved)
        if code == 200 and good_entity(payload):
            entity_ok += 1
            ok += 1
        else:
            gaps.append(f"GET {resolved} -> {code}")

    _, vms = get("/ovirt-engine/api/vms")
    _, hosts = get("/ovirt-engine/api/hosts")
    _, dcs = get("/ovirt-engine/api/datacenters")
    print(f"ENGINE={ENGINE} SERIES={SERIES}")
    print(
        f"DUMP {ok}/{probed} contract GETs "
        f"(collections+entities; entities {entity_ok}/{entity_probed})"
    )
    print(
        f"DENSITY vms={len(items(vms))} hosts={len(items(hosts))} "
        f"datacenters={len(items(dcs))} inventory_keys={len(inventory)}"
    )
    if gaps:
        print(f"GAPS ({len(gaps)}):")
        for g in gaps:
            print(" ", g)
    else:
        print("GAPS: none")
    return 0 if not gaps and ok == probed else 1


if __name__ == "__main__":
    raise SystemExit(main())
