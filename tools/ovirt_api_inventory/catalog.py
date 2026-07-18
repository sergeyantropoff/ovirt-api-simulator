"""Master inventory of oVirt Engine REST API collections, actions, and series deltas.

Derived from the official oVirt Engine API model
(https://ovirt.github.io/ovirt-engine-api-model/).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]
ApiVersion = Literal["3", "4"]

# Engine release series supported by the simulator.
SERIES: tuple[str, ...] = (
    "3.0",
    "3.1",
    "3.2",
    "3.3",
    "3.4",
    "3.5",
    "3.6",
    "4.3",
    "4.4",
    "4.5",
    "master",
)

SERIES_MAJOR: dict[str, int] = {
    "3.0": 30,
    "3.1": 31,
    "3.2": 32,
    "3.3": 33,
    "3.4": 34,
    "3.5": 35,
    "3.6": 36,
    "4.3": 43,
    "4.4": 44,
    "4.5": 45,
    "master": 50,
}

SERIES_PRODUCT: dict[str, dict[str, str]] = {
    "3.0": {"major": "3", "minor": "0", "full": "3.0.0"},
    "3.1": {"major": "3", "minor": "1", "full": "3.1.0"},
    "3.2": {"major": "3", "minor": "2", "full": "3.2.0"},
    "3.3": {"major": "3", "minor": "3", "full": "3.3.0"},
    "3.4": {"major": "3", "minor": "4", "full": "3.4.0"},
    "3.5": {"major": "3", "minor": "5", "full": "3.5.0"},
    "3.6": {"major": "3", "minor": "6", "full": "3.6.0"},
    "4.3": {"major": "4", "minor": "3", "full": "4.3.0"},
    "4.4": {"major": "4", "minor": "4", "full": "4.4.0"},
    "4.5": {"major": "4", "minor": "5", "full": "4.5.0"},
    "master": {"major": "4", "minor": "6", "full": "4.6.0-master"},
}


@dataclass(frozen=True)
class CollectionSpec:
    """Top-level or nested collection in the Engine API."""

    path: str  # e.g. datacenters, vms/{vm_id}/nics
    name: str  # collection element name (plural path segment)
    element: str  # singular XML/JSON element
    introduced_in: str = "3.0"
    removed_in: str | None = None
    search: bool = True
    actions: tuple[str, ...] = ()
    subcollections: tuple[str, ...] = ()
    api_versions: tuple[ApiVersion, ...] = ("3", "4")
    notes: str = ""


@dataclass(frozen=True)
class ActionSpec:
    path_suffix: str
    introduced_in: str = "3.0"
    removed_in: str | None = None
    api_versions: tuple[ApiVersion, ...] = ("3", "4")


# Top-level collections from the Api entry point (rel links).
TOP_LEVEL: tuple[CollectionSpec, ...] = (
    CollectionSpec("affinitylabels", "affinitylabels", "affinity_label", introduced_in="4.3"),
    CollectionSpec("bookmarks", "bookmarks", "bookmark"),
    CollectionSpec("clusterlevels", "clusterlevels", "cluster_level", introduced_in="3.6", search=False),
    CollectionSpec(
        "clusters",
        "clusters",
        "cluster",
        actions=("resetemulatedmachine", "syncallnetworks", "upgrade", "refreshglusterhealstatus"),
        subcollections=(
            "networks",
            "permissions",
            "glustervolumes",
            "affinitygroups",
            "cpuprofiles",
            "enabledfeatures",
        ),
    ),
    CollectionSpec(
        "datacenters",
        "datacenters",
        "data_center",
        actions=("cleanfinishedtasks",),
        subcollections=("clusters", "storagedomains", "permissions", "networks", "quotas", "qoss", "iscsibonds"),
    ),
    CollectionSpec(
        "disks",
        "disks",
        "disk",
        actions=("copy", "export", "move", "sparsify", "reduce"),
        subcollections=("permissions", "statistics"),
    ),
    CollectionSpec("domains", "domains", "domain", search=False, subcollections=("users", "groups")),
    CollectionSpec("events", "events", "event"),
    CollectionSpec(
        "externalhostproviders",
        "externalhostproviders",
        "external_host_provider",
        introduced_in="3.4",
        subcollections=("computeresources", "discoveredhosts", "hostgroups", "hosts"),
    ),
    CollectionSpec("groups", "groups", "group", subcollections=("roles", "permissions", "tags")),
    CollectionSpec(
        "hosts",
        "hosts",
        "host",
        actions=(
            "activate",
            "deactivate",
            "approve",
            "install",
            "fence",
            "iscsidiscover",
            "iscsilogin",
            "commitnetconfig",
            "refresh",
            "unregisteredstoragedomainsdiscover",
            "upgrade",
            "upgradeCheck",
            "enrollcertificate",
        ),
        subcollections=("nics", "storage", "tags", "permissions", "statistics", "hooks", "devices", "katelloerrata"),
    ),
    CollectionSpec("icons", "icons", "icon", introduced_in="3.6", search=False),
    CollectionSpec("instancetypes", "instancetypes", "instance_type", introduced_in="3.5"),
    CollectionSpec("jobs", "jobs", "job", introduced_in="3.1", search=False, subcollections=("steps",)),
    CollectionSpec("katelloerrata", "katelloerrata", "katello_erratum", introduced_in="3.5"),
    CollectionSpec("macpools", "macpools", "mac_pool", introduced_in="3.6"),
    CollectionSpec("networkfilters", "networkfilters", "network_filter", introduced_in="3.6", search=False),
    CollectionSpec(
        "networks",
        "networks",
        "network",
        subcollections=("permissions", "vnicprofiles", "networklabels"),
    ),
    CollectionSpec(
        "openstackimageproviders",
        "openstackimageproviders",
        "openstack_image_provider",
        introduced_in="3.3",
        subcollections=("images", "certificates"),
    ),
    CollectionSpec(
        "openstacknetworkproviders",
        "openstacknetworkproviders",
        "openstack_network_provider",
        introduced_in="3.3",
        subcollections=("networks", "certificates"),
    ),
    CollectionSpec(
        "openstackvolumeproviders",
        "openstackvolumeproviders",
        "openstack_volume_provider",
        introduced_in="3.4",
        subcollections=("volumetypes", "authenticationkeys", "certificates"),
    ),
    CollectionSpec("operatingsystems", "operatingsystems", "operating_system", introduced_in="3.5", search=False),
    CollectionSpec("permissions", "permissions", "permission", search=False),
    CollectionSpec("roles", "roles", "role", subcollections=("permits",)),
    CollectionSpec(
        "schedulingpolicies",
        "schedulingpolicies",
        "scheduling_policy",
        introduced_in="3.3",
        subcollections=("filters", "weights", "balances"),
    ),
    CollectionSpec(
        "schedulingpolicyunits",
        "schedulingpolicyunits",
        "scheduling_policy_unit",
        introduced_in="3.3",
        search=False,
    ),
    CollectionSpec("storageconnections", "storageconnections", "storage_connection"),
    CollectionSpec(
        "storagedomains",
        "storagedomains",
        "storage_domain",
        actions=("refreshluns", "updateovfstore", "reduceluns"),
        subcollections=("disks", "files", "templates", "vms", "storageconnections", "permissions", "diskprofiles", "images"),
    ),
    CollectionSpec("tags", "tags", "tag"),
    CollectionSpec(
        "templates",
        "templates",
        "template",
        actions=("export",),
        subcollections=("diskattachments", "nics", "cdroms", "tags", "permissions", "graphicsconsoles", "watchdogs", "mediateddevices"),
    ),
    CollectionSpec("users", "users", "user", subcollections=("roles", "permissions", "tags", "options", "sshpublickeys")),
    CollectionSpec("vmpools", "vmpools", "vm_pool", subcollections=("permissions",)),
    CollectionSpec(
        "vms",
        "vms",
        "vm",
        actions=(
            "start",
            "stop",
            "shutdown",
            "reboot",
            "suspend",
            "migrate",
            "cancelmigration",
            "clone",
            "export",
            "detach",
            "screenthumbnail",
            "ticket",
            "logon",
            "maintenance",
            "preview_snapshot",
            "commit_snapshot",
            "undo_snapshot",
            "freeze_filesystems",
            "thaw_filesystems",
        ),
        subcollections=(
            "diskattachments",
            "nics",
            "cdroms",
            "snapshots",
            "tags",
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
        ),
    ),
    CollectionSpec(
        "vnicprofiles",
        "vnicprofiles",
        "vnic_profile",
        introduced_in="3.3",
        subcollections=("permissions",),
    ),
    CollectionSpec("imageTransfers", "imagetransfers", "image_transfer", introduced_in="4.3", search=False),
    CollectionSpec("options", "options", "engine_option", introduced_in="4.4", search=False),
)

# Nested collections relative to parent resource path.
NESTED: tuple[CollectionSpec, ...] = (
    CollectionSpec("vms/{vm_id}/diskattachments", "diskattachments", "disk_attachment", search=False),
    CollectionSpec(
        "vms/{vm_id}/nics",
        "nics",
        "nic",
        search=False,
        actions=("activate", "deactivate"),
        subcollections=("networkfilterparameters",),
    ),
    CollectionSpec("vms/{vm_id}/cdroms", "cdroms", "cdrom", search=False),
    CollectionSpec(
        "vms/{vm_id}/snapshots",
        "snapshots",
        "snapshot",
        search=False,
        actions=("restore",),
        subcollections=("disks", "nics", "cdroms"),
    ),
    CollectionSpec("vms/{vm_id}/tags", "tags", "tag", search=False),
    CollectionSpec("vms/{vm_id}/permissions", "permissions", "permission", search=False),
    CollectionSpec("vms/{vm_id}/graphicsconsoles", "graphicsconsoles", "graphics_console", search=False, introduced_in="3.5"),
    CollectionSpec("hosts/{host_id}/nics", "nics", "host_nic", search=False, actions=("update", "attach", "detach")),
    CollectionSpec("hosts/{host_id}/tags", "tags", "tag", search=False),
    CollectionSpec("hosts/{host_id}/permissions", "permissions", "permission", search=False),
    CollectionSpec("hosts/{host_id}/statistics", "statistics", "statistic", search=False),
    CollectionSpec(
        "clusters/{cluster_id}/affinitygroups",
        "affinitygroups",
        "affinity_group",
        introduced_in="3.3",
        search=False,
        subcollections=("vms", "hosts"),
    ),
    CollectionSpec("clusters/{cluster_id}/networks", "networks", "network", search=False),
    CollectionSpec("clusters/{cluster_id}/permissions", "permissions", "permission", search=False),
    CollectionSpec(
        "datacenters/{datacenter_id}/storagedomains",
        "storagedomains",
        "storage_domain",
        search=False,
        actions=("activate", "deactivate"),
    ),
    CollectionSpec("datacenters/{datacenter_id}/clusters", "clusters", "cluster", search=False),
    CollectionSpec("datacenters/{datacenter_id}/networks", "networks", "network", search=False),
    CollectionSpec("datacenters/{datacenter_id}/quotas", "quotas", "quota", search=False, introduced_in="3.1"),
    CollectionSpec("datacenters/{datacenter_id}/permissions", "permissions", "permission", search=False),
    CollectionSpec("networks/{network_id}/vnicprofiles", "vnicprofiles", "vnic_profile", search=False, introduced_in="3.3"),
    CollectionSpec("templates/{template_id}/diskattachments", "diskattachments", "disk_attachment", search=False),
    CollectionSpec("templates/{template_id}/nics", "nics", "nic", search=False),
    CollectionSpec("storagedomains/{storagedomain_id}/disks", "disks", "disk", search=False),
    CollectionSpec("storagedomains/{storagedomain_id}/files", "files", "file", search=False),
    CollectionSpec("jobs/{job_id}/steps", "steps", "step", search=False, introduced_in="3.1"),
)

# Resources / actions introduced (or changed) per series — real deltas, not copies.
SERIES_INTRODUCED_PATHS: dict[str, tuple[str, ...]] = {
    "3.0": (),
    "3.1": ("/jobs", "/datacenters/{id}/quotas"),
    "3.2": ("/disks/{id}/export", "/vms/{id}/logon"),
    "3.3": (
        "/vnicprofiles",
        "/schedulingpolicies",
        "/schedulingpolicyunits",
        "/openstackimageproviders",
        "/openstacknetworkproviders",
        "/clusters/{id}/affinitygroups",
    ),
    "3.4": ("/externalhostproviders", "/openstackvolumeproviders", "/hosts/{id}/unregisteredstoragedomainsdiscover"),
    "3.5": ("/instancetypes", "/operatingsystems", "/katelloerrata", "/vms/{id}/graphicsconsoles", "/vms/{id}/maintenance"),
    "3.6": ("/clusterlevels", "/icons", "/macpools", "/networkfilters", "/hosts/{id}/upgrade", "/vms/{id}/numanodes"),
    "4.3": ("/affinitylabels", "/imagetransfers", "/vms/{id}/affinitylabels", "/hosts/{id}/enrollcertificate"),
    "4.4": ("/options", "/disks/{id}/reduce", "/storagedomains/{id}/reduceluns"),
    "4.5": ("/vms/{id}/mediateddevices", "/templates/{id}/mediateddevices", "/clusters/{id}/enabledfeatures"),
    "master": ("/vms/{id}/externaldata", "/hosts/{id}/upgradecheck"),
}

# Collections removed or deprecated relative to prior series (v3-era naming).
SERIES_REMOVED_PATHS: dict[str, tuple[str, ...]] = {
    "4.3": ("/storage",),  # legacy v3 /storage entry no longer advertised in v4 packs
}


def series_index(series: str) -> int:
    return SERIES.index(series)


def available_in(series: str, introduced_in: str, removed_in: str | None = None) -> bool:
    if series_index(series) < series_index(introduced_in):
        return False
    if removed_in is not None and series_index(series) >= series_index(removed_in):
        return False
    return True


def api_version_for_series(series: str) -> ApiVersion:
    return "3" if series.startswith("3.") else "4"


def collections_for_series(series: str) -> list[CollectionSpec]:
    out: list[CollectionSpec] = []
    for spec in (*TOP_LEVEL, *NESTED):
        if available_in(series, spec.introduced_in, spec.removed_in):
            av = api_version_for_series(series)
            if av in spec.api_versions:
                out.append(spec)
    return out


@dataclass
class Operation:
    operation_id: str
    method: HttpMethod
    path: str
    resource_type: str
    collection_key: str
    element: str
    kind: Literal["root", "collection", "item", "action", "subcollection"] = "collection"
    search: bool = False
    introduced_in: str = "3.0"
    notes: str = ""


def _ops_for_collection(spec: CollectionSpec, *, api_prefix: str) -> list[Operation]:
    base = f"{api_prefix}/{spec.path}"
    element = spec.element
    name = spec.name
    ops: list[Operation] = [
        Operation(
            f"{name}.list",
            "GET",
            base,
            element,
            name,
            element,
            kind="collection",
            search=spec.search,
            introduced_in=spec.introduced_in,
            notes=spec.notes or f"List {name}",
        ),
        Operation(
            f"{name}.add",
            "POST",
            base,
            element,
            name,
            element,
            kind="collection",
            introduced_in=spec.introduced_in,
            notes=f"Add {element}",
        ),
    ]
    # Item path: replace trailing collection with {id} or use last segment id
    if "{" in spec.path and not spec.path.endswith("}"):
        item_path = f"{base}/{{id}}"
    elif "{" in spec.path:
        # nested already ends with param — treat as item collection parent
        item_path = f"{base}/{{id}}"
    else:
        item_path = f"{base}/{{id}}"

    ops.extend(
        [
            Operation(
                f"{name}.get",
                "GET",
                item_path,
                element,
                name,
                element,
                kind="item",
                introduced_in=spec.introduced_in,
            ),
            Operation(
                f"{name}.update",
                "PUT",
                item_path,
                element,
                name,
                element,
                kind="item",
                introduced_in=spec.introduced_in,
            ),
            Operation(
                f"{name}.remove",
                "DELETE",
                item_path,
                element,
                name,
                element,
                kind="item",
                introduced_in=spec.introduced_in,
            ),
        ]
    )
    for action in spec.actions:
        if not available_in(spec.introduced_in, spec.introduced_in):
            continue
        ops.append(
            Operation(
                f"{name}.{action}",
                "POST",
                f"{item_path}/{action}",
                element,
                name,
                element,
                kind="action",
                introduced_in=spec.introduced_in,
                notes=f"Action {action}",
            )
        )
    return ops


def build_operations(series: str) -> list[Operation]:
    """Build the full operation list for a series pack (both /api and /api/vN prefixes)."""

    api_ver = api_version_for_series(series)
    prefixes = [f"/ovirt-engine/api", f"/ovirt-engine/api/v{api_ver}"]
    ops: list[Operation] = []
    for prefix in prefixes:
        ops.append(
            Operation(
                "api.get",
                "GET",
                prefix if not prefix.endswith("/api") else "/ovirt-engine/api"
                if prefix == "/ovirt-engine/api"
                else prefix,
                "api",
                "api",
                "api",
                kind="root",
                introduced_in="3.0",
                notes="API entry point",
            )
        )
        # Avoid duplicate root for second prefix when first is already /ovirt-engine/api
        if prefix == "/ovirt-engine/api":
            root_path = "/ovirt-engine/api"
        else:
            root_path = prefix
        # fix root op path
        ops[-1] = Operation(
            "api.get" if prefix == "/ovirt-engine/api" else f"api.v{api_ver}.get",
            "GET",
            root_path,
            "api",
            "api",
            "api",
            kind="root",
            introduced_in="3.0",
            notes="API entry point",
        )
        for spec in collections_for_series(series):
            for op in _ops_for_collection(spec, api_prefix=prefix):
                # Filter actions introduced later than series via SERIES_INTRODUCED_PATHS
                if op.kind == "action":
                    action_path = "/" + "/".join(op.path.split("/")[3:])  # rough
                    skip = False
                    for intro_series, paths in SERIES_INTRODUCED_PATHS.items():
                        if series_index(series) < series_index(intro_series):
                            for p in paths:
                                if p.rstrip("/").split("/")[-1] == op.path.rstrip("/").split("/")[-1] and "{" in p:
                                    # only skip if this action path was introduced later
                                    if op.path.endswith("/" + p.rstrip("/").split("/")[-1]):
                                        if any(op.path.endswith(x.split("/")[-1]) for x in paths):
                                            # Check precise: action name in introduced paths for later series
                                            pass
                    # Simpler filter: action introduced with collection unless in later SERIES_INTRODUCED
                    for intro_series, paths in SERIES_INTRODUCED_PATHS.items():
                        if series_index(series) < series_index(intro_series):
                            for p in paths:
                                suffix = p.split("/")[-1]
                                if op.path.endswith("/" + suffix) and "{" in p:
                                    skip = True
                                    break
                        if skip:
                            break
                    if skip:
                        continue
                ops.append(op)

        # Extra series-specific action paths not in CollectionSpec.actions
        for intro_series, paths in SERIES_INTRODUCED_PATHS.items():
            if not available_in(series, intro_series):
                continue
            for p in paths:
                if not p.startswith("/"):
                    continue
                # Only add action POST ops for paths that look like actions (contain {id}/name)
                parts = p.strip("/").split("/")
                if len(parts) >= 2 and parts[-2].startswith("{") is False and "{" in p:
                    # e.g. /vms/{id}/logon
                    full = f"{prefix}{p}".replace("{id}", "{id}")
                    # normalize {vm_id} style
                    full = full.replace("{id}", "{id}")
                    if any(x in p for x in ("/{id}/", "/{vm_id}/", "/{host_id}/", "/{cluster_id}/")):
                        action = parts[-1]
                        parent = parts[0]
                        # skip if already present
                        if any(o.path == f"{prefix}{p}".replace("{vm_id}", "{id}").replace("{host_id}", "{id}") for o in ops):
                            continue
                        norm = p
                        for alias in ("vm_id", "host_id", "cluster_id", "datacenter_id", "network_id", "template_id", "storagedomain_id", "job_id"):
                            norm = norm.replace("{" + alias + "}", "{id}")
                        full_path = f"{prefix}{norm}"
                        if any(o.path == full_path and o.method == "POST" for o in ops):
                            continue
                        if "{" in p and not p.endswith("}"):
                            ops.append(
                                Operation(
                                    f"{parent}.{action}",
                                    "POST",
                                    full_path,
                                    parent.rstrip("s") if parent.endswith("s") else parent,
                                    parent,
                                    parent.rstrip("s") if parent.endswith("s") else parent,
                                    kind="action",
                                    introduced_in=intro_series,
                                    notes=f"Series delta action {action}",
                                )
                            )

    # Deduplicate by method+path
    seen: set[tuple[str, str]] = set()
    unique: list[Operation] = []
    for op in ops:
        key = (op.method, op.path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(op)
    return unique


def entry_point_links(series: str) -> list[dict[str, str]]:
    links = []
    for spec in TOP_LEVEL:
        if available_in(series, spec.introduced_in, spec.removed_in):
            links.append({"rel": spec.name, "href": f"/ovirt-engine/api/{spec.path.split('/')[0]}"})
    return links
