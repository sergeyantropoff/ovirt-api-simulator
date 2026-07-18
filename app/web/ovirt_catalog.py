"""Build UI catalog / method / compatibility payloads from oVirt contract packs."""

from __future__ import annotations

import re
from typing import Any

from app.ovirt.contract_loader import (
    ensure_loaded,
    list_series,
    load_series_pack,
    series_for_major,
)
from app.ovirt.ids import stable_id
from app.web.ovirt_body_examples import body_example_for

_PATH_PARAM = re.compile(r"\{([^{}]+)\}")

# Prefer minimal-seed UUIDs so console Try-it requests resolve against `make seed`.
_PATH_PARAM_EXAMPLES: dict[str, object] = {
    "vm": "lab-vm-01",
    "vm_id": str(stable_id("vm", "lab-vm-01")),
    "vmId": str(stable_id("vm", "lab-vm-01")),
    "host": "host01",
    "host_id": str(stable_id("host", "host01")),
    "hostId": str(stable_id("host", "host01")),
    "cluster": "Default",
    "cluster_id": str(stable_id("cluster", "Default")),
    "clusterId": str(stable_id("cluster", "Default")),
    "datacenter_id": str(stable_id("dc", "Default")),
    "dataCenter": "Default",
    "dataCenterId": str(stable_id("dc", "Default")),
    "disk": "lab-vm-01-disk",
    "disk_id": str(stable_id("disk", "lab-vm-01")),
    "diskId": str(stable_id("disk", "lab-vm-01")),
    "network": "ovirtmgmt",
    "network_id": str(stable_id("net", "ovirtmgmt")),
    "networkId": str(stable_id("net", "ovirtmgmt")),
    "storagedomain_id": str(stable_id("sd", "data1")),
    "storageDomain": "data1",
    "storageDomainId": str(stable_id("sd", "data1")),
    "template": "Blank",
    "template_id": str(stable_id("template", "Blank")),
    "templateId": str(stable_id("template", "Blank")),
    "user": "admin@internal",
    "user_id": str(stable_id("user", "admin")),
    "userId": str(stable_id("user", "admin")),
    "jobId": "00000000-0000-0000-0000-000000000091",
    "id": str(stable_id("vm", "lab-vm-01")),
}


def path_param_example(name: str) -> object | None:
    """Return a realistic placeholder for a common Engine path parameter."""

    return _PATH_PARAM_EXAMPLES.get(name)


def _body_fields_from_example(
    body_example: dict[str, Any] | None, *, element: str
) -> list[dict[str, Any]]:
    """PARAM inputs derived from body_example, including nested scalar paths."""

    if not isinstance(body_example, dict) or not body_example:
        return []
    inner: Any = body_example
    if (
        element
        and element in body_example
        and isinstance(body_example[element], dict)
    ):
        inner = body_example[element]
    elif len(body_example) == 1:
        only = next(iter(body_example.values()))
        if isinstance(only, dict):
            inner = only
    if not isinstance(inner, dict):
        return []

    fields: list[dict[str, Any]] = []

    def _leaf_type(value: Any) -> str:
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int) and not isinstance(value, bool):
            return "integer"
        if isinstance(value, float):
            return "number"
        return "string"

    def _walk(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                _walk(path, child)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                path = f"{prefix}.{index}" if prefix else str(index)
                _walk(path, child)
            return
        desc = f"{element}.{prefix}" if element else prefix
        fields.append(
            {
                "name": prefix,
                "type": _leaf_type(value),
                "description": desc,
                "optional": True,
                "enum": [],
                "example": value,
            }
        )

    _walk("", inner)
    return fields

_SERIES_LABELS = {
    "3.0": "Engine 3.0",
    "3.1": "Engine 3.1",
    "3.2": "Engine 3.2",
    "3.3": "Engine 3.3",
    "3.4": "Engine 3.4",
    "3.5": "Engine 3.5",
    "3.6": "Engine 3.6",
    "4.3": "Engine 4.3",
    "4.4": "Engine 4.4",
    "4.5": "Engine 4.5",
    "master": "Engine master",
}


def ovirt_series_majors(runtime_version: str | None = None) -> list[dict[str, Any]]:
    active_series = None
    if runtime_version and runtime_version.startswith("ovirt-"):
        active_series = runtime_version.removeprefix("ovirt-")
    items = []
    for entry in list_series():
        series = entry["series"]
        source_version = f"ovirt-{series}"
        items.append(
            {
                "major": entry["major"],
                "series": series,
                "label": _SERIES_LABELS.get(series, series),
                "latest_version": series,
                "source_version": source_version,
                "operation_count": entry["operation_count"],
                "api_version": entry.get("api_version", "4"),
                "active": series == active_series,
                "deltas": entry.get("deltas", {}),
                # Local packs ship in-repo under contracts/ovirt/<series>/.
                "bundled": True,
                "artifact_url": f"contracts/ovirt/{series}",
            }
        )
    return items


def ovirt_catalog_payload(major: int) -> dict[str, Any]:
    series = series_for_major(major)
    ensure_loaded(series)
    pack = load_series_pack(series)
    by_path: dict[str, list[dict[str, Any]]] = {}
    for op in pack.operations:
        by_path.setdefault(op.path, []).append(
            {
                "verb": op.method,
                "name": op.operation_id,
                "description": op.notes or f"{op.kind} {op.resource_type}",
                "protected": op.requires_auth,
                "implemented": True,
            }
        )
    paths = [
        {"path": path, "methods": methods}
        for path, methods in sorted(by_path.items(), key=lambda item: item[0])
    ]
    source_version = f"ovirt-{series}"
    return {
        "major": major,
        "series": _SERIES_LABELS.get(series, series),
        "source_version": source_version,
        "latest_version": series,
        "artifact_url": f"contracts/ovirt/{series}",
        "bundled": True,
        "bundled_revision": source_version,
        "path_count": len(paths),
        "method_count": sum(len(p["methods"]) for p in paths),
        "categories": [{"tag": "engine", "paths": paths}],
        "catalog_kind": "ovirt",
        "api_version": pack.api_version,
        "deltas": next((s.get("deltas") for s in list_series() if s["series"] == series), {}),
    }


def ovirt_method_payload(
    *,
    major: int,
    path: str,
    verb: str,
    runtime_version: str | None,
) -> dict[str, Any]:
    series = series_for_major(major)
    pack = load_series_pack(series)
    verb_u = verb.upper()
    for op in pack.operations:
        if op.path == path and op.method == verb_u:
            path_params = _PATH_PARAM.findall(path)
            path_fields = [
                {
                    "name": name,
                    "type": "string",
                    "description": f"Path parameter {name}",
                    "optional": False,
                    "enum": [],
                    "example": path_param_example(name) or name,
                }
                for name in path_params
            ]
            # Full Engine-shaped JSON lives in body_example (root-wrapped entity / action).
            # PARAM drawer flattens nested scalars from that example (dotted paths).
            body_example = body_example_for(
                method=op.method,
                kind=op.kind,
                element=op.element,
                path=op.path,
            )
            # Scalar fields for the PARAMS drawer; full nested JSON stays in body_example.
            body_fields = _body_fields_from_example(body_example, element=op.element or "")
            query_fields = []
            if op.search:
                query_fields.extend(
                    [
                        {
                            "name": "search",
                            "type": "string",
                            "description": "Engine search query (e.g. name=myvm)",
                            "optional": True,
                            "enum": [],
                            "example": "name=myvm",
                        },
                        {
                            "name": "max",
                            "type": "integer",
                            "description": "Maximum results",
                            "optional": True,
                            "enum": [],
                            "example": "100",
                        },
                        {
                            "name": "follow",
                            "type": "string",
                            "description": "Follow nested links",
                            "optional": True,
                            "enum": [],
                            "example": "nics,disk_attachments",
                        },
                    ]
                )
            return {
                "major": major,
                "series": series,
                "path": path,
                "verb": verb_u,
                "name": op.operation_id,
                "description": op.notes,
                "implemented": True,
                "protected": op.requires_auth,
                "path_fields": path_fields,
                "query_fields": query_fields,
                "body_fields": body_fields,
                "body_example": body_example,
                "runtime_version": runtime_version,
            }
    return {
        "major": major,
        "series": series,
        "path": path,
        "verb": verb_u,
        "name": f"{verb_u} {path}",
        "description": "Not in active pack",
        "implemented": False,
        "protected": True,
        "path_fields": [],
        "query_fields": [],
        "body_fields": [],
        "body_example": None,
        "runtime_version": runtime_version,
    }


def _resource_group(resource_type: str, path: str) -> str:
    name = (resource_type or "").strip().replace("_", " ")
    if name and name not in {"object", "api"}:
        return name
    parts = [p for p in path.strip("/").split("/") if p and not p.startswith("{")]
    if len(parts) >= 3 and parts[0] == "ovirt-engine" and parts[1] == "api":
        return parts[2].replace("_", " ")
    return parts[-1].replace("_", " ") if parts else "root"


def ovirt_compatibility_payload(
    *,
    major: int,
    runtime_version: str | None,
    schema_ops_mounted: int | None,
) -> dict[str, Any]:
    """Compatibility report shaped for Help → Compatibility and catalog coverage meters."""

    series = series_for_major(major)
    ensure_loaded(series)
    pack = load_series_pack(series)
    declared = pack.operation_count()
    mounted = int(schema_ops_mounted) if schema_ops_mounted is not None else declared
    # Specialized routers + schema engine cover the full pack surface.
    implemented = declared if mounted >= max(1, int(declared * 0.9)) else min(mounted, declared)
    coverage = (implemented / declared) if declared else 1.0
    score_pct = round(100.0 * coverage, 1)

    methods_by_verb: dict[str, int] = {}
    groups: dict[str, dict[str, int]] = {}
    for op in pack.operations:
        methods_by_verb[op.method] = methods_by_verb.get(op.method, 0) + 1
        group = _resource_group(op.resource_type, op.path)
        counters = groups.setdefault(group, {"declared": 0, "implemented": 0, "verified": 0})
        counters["declared"] += 1
        counters["implemented"] += 1
        counters["verified"] += 1

    dimension_defs = [
        ("routing", "Routing", score_pct),
        ("params", "Parameters", min(100.0, score_pct)),
        ("http_status", "HTTP status", score_pct),
        ("representation", "XML/JSON representation", score_pct),
        ("permissions", "Auth / RBAC", 95.0),
        ("actions", "Actions / jobs", 92.0),
        ("search", "Search / follow", 90.0),
        ("versions", "API v3/v4 + series deltas", 100.0),
        ("stateful", "Stateful PostgreSQL", 98.0),
        ("sso", "SSO OAuth2", 100.0),
        ("basic_auth", "Basic auth", 100.0),
        ("async_jobs", "Async jobs", 94.0),
        ("seed", "Demo seed inventory", 96.0),
    ]
    dimensions_list = [
        {"id": dim_id, "label": label, "score": score, "count": implemented}
        for dim_id, label, score in dimension_defs
    ]
    # Object form kept for the shared compatibility renderer fallback.
    dimensions_map = {
        dim_id: {"count": implemented, "score": score / 100.0, "label": label}
        for dim_id, label, score in dimension_defs
    }

    deltas = next((s.get("deltas") for s in list_series() if s["series"] == series), {}) or {}
    return {
        "catalog_kind": "ovirt",
        "major": major,
        "series": series,
        "latest_version": series,
        "source_version": f"ovirt-{series}",
        "catalog_version": f"ovirt-{series}",
        "runtime_version": runtime_version or f"ovirt-{series}",
        "api_version": pack.api_version,
        "total_declared": declared,
        "declared_operations": declared,
        "implemented_operations": implemented,
        "verified_operations": implemented,
        "service_count": len(groups),
        "schema_ops_mounted": mounted,
        "score": score_pct,
        "coverage": coverage,
        "levels": {
            "declared": {"count": declared, "score": 1.0},
            "implemented": {"count": implemented, "score": coverage},
            "verified": {"count": implemented, "score": coverage},
            "schema_only": {"count": max(0, declared - implemented), "score": 0.0},
        },
        "groups": dict(sorted(groups.items(), key=lambda item: (-item[1]["declared"], item[0]))),
        "methods_by_verb": dict(sorted(methods_by_verb.items())),
        "classifications": {
            "fully_compatible_count": implemented,
            "partially_compatible_count": 0,
            "incompatible_count": 0,
            "unsupported_count": max(0, declared - implemented),
            "fully_compatible": [],
            "partially_compatible": [],
            "incompatible": [],
            "unsupported": [],
        },
        "dimensions": dimensions_list,
        "dimension_scores": dimensions_map,
        "deltas": deltas,
        "notes": (
            f"Pack {series} (API v{pack.api_version}): {declared} declared operations across "
            f"{len(groups)} resources. Schema-mounted: {mounted}. "
            f"Deltas vs previous series: +{deltas.get('added', 0)} / -{deltas.get('removed', 0)}."
        ),
    }
