"""OpenAPI tag resolution for Engine API and simulator routes."""

from __future__ import annotations

_COLLECTION_LABELS: dict[str, str] = {
    "vms": "VMs",
    "disks": "Disks",
    "hosts": "Hosts",
    "clusters": "Clusters",
    "datacenters": "Data Centers",
    "networks": "Networks",
    "vnicprofiles": "vNIC Profiles",
    "storagedomains": "Storage Domains",
    "storageconnections": "Storage Connections",
    "templates": "Templates",
    "users": "Users",
    "groups": "Groups",
    "roles": "Roles",
    "permissions": "Permissions",
    "domains": "Domains",
    "events": "Events",
    "jobs": "Jobs",
    "tags": "Tags",
    "bookmarks": "Bookmarks",
    "affinitylabels": "Affinity Labels",
    "instancetypes": "Instance Types",
    "macpools": "MAC Pools",
    "schedulingpolicies": "Scheduling Policies",
    "schedulingpolicyunits": "Scheduling Policy Units",
    "clusterlevels": "Cluster Levels",
    "icons": "Icons",
    "operatingsystems": "Operating Systems",
    "networkfilters": "Network Filters",
    "vmpools": "VM Pools",
    "katelloerrata": "Katello Errata",
    "externalhostproviders": "External Host Providers",
    "openstacknetworkproviders": "OpenStack Network Providers",
    "openstackimageproviders": "OpenStack Image Providers",
    "openstackvolumeproviders": "OpenStack Volume Providers",
    "imagetransfers": "Image Transfers",
    "options": "Options",
}


def contract_openapi_tag(path: str) -> str:
    """Map an Engine API path to a Swagger UI category."""

    parts = [part for part in path.strip("/").split("/") if part]
    if parts[:2] == ["ovirt-engine", "api"]:
        parts = parts[2:]
    if parts and parts[0] in {"v3", "v4"}:
        parts = parts[1:]
    if not parts:
        return "engine"
    root = parts[0]
    return _COLLECTION_LABELS.get(root, root.replace("-", " ").title())


def contract_openapi_tags(path: str, renderer: str | None = None) -> list[str]:
    """Return OpenAPI tags for a contract route.

    ``renderer`` is accepted for call-site compatibility; Engine API has a
    single representation surface.
    """

    del renderer
    return [contract_openapi_tag(path)]


def openapi_tag_metadata() -> list[dict[str, str]]:
    """Descriptions shown in Swagger UI for each tag group."""

    tags: list[dict[str, str]] = [
        {
            "name": "engine",
            "description": "oVirt Engine REST API root under `/ovirt-engine/api`.",
        },
        {
            "name": "sso",
            "description": "Engine SSO OAuth2 token endpoints.",
        },
        {
            "name": "Simulator",
            "description": "Health checks, compatibility reports, and the web console.",
        },
    ]
    for label in sorted(set(_COLLECTION_LABELS.values())):
        tags.append(
            {
                "name": label,
                "description": f"Engine {label} collection under `/ovirt-engine/api`.",
            }
        )
    return tags
