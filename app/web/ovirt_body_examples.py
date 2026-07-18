"""Engine-shaped JSON request-body examples for the Web console.

Bodies follow the oVirt Engine REST convention: a single root element wrapping
the resource (or ``action``). Field shapes match what this simulator accepts and
what the public Engine API model documents for common create/update/action calls.
"""

from __future__ import annotations

from typing import Any

from app.ovirt.ids import stable_id

# Minimal-seed stable IDs (see app.ovirt.seed) — usable with `make seed`.
_DC = str(stable_id("dc", "Default"))
_CLUSTER = str(stable_id("cluster", "Default"))
_HOST = str(stable_id("host", "host01"))
_TEMPLATE = str(stable_id("template", "Blank"))
_SD = str(stable_id("sd", "data1"))
_NET = str(stable_id("net", "ovirtmgmt"))
_VNIC = str(stable_id("vnic", "ovirtmgmt"))
_VM = str(stable_id("vm", "lab-vm-01"))
_DISK = str(stable_id("disk", "lab-vm-01"))
_USER = str(stable_id("user", "admin"))
_ROLE = str(stable_id("role", "SuperUser"))
_DOMAIN = str(stable_id("domain", "internal"))


def _ref(collection: str, object_id: str, *, name: str | None = None) -> dict[str, Any]:
    entity: dict[str, Any] = {
        "id": object_id,
        "href": f"/ovirt-engine/api/{collection}/{object_id}",
    }
    if name is not None:
        entity["name"] = name
    return entity


def _wrap(element: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {element: payload}


def _entity_bodies() -> dict[str, dict[str, Any]]:
    """Map contract ``element`` → inner payload (without root wrapper)."""

    return {
        "vm": {
            "name": "example-vm",
            "description": "Example virtual machine",
            "type": "server",
            "memory": 1073741824,
            "cpu": {"topology": {"sockets": 1, "cores": 1, "threads": 1}},
            "os": {"type": "other"},
            "cluster": _ref("clusters", _CLUSTER, name="Default"),
            "template": _ref("templates", _TEMPLATE, name="Blank"),
        },
        "host": {
            "name": "host-02",
            "address": "192.168.1.11",
            "comment": "Example host",
            "cluster": _ref("clusters", _CLUSTER, name="Default"),
        },
        "disk": {
            "name": "example-disk",
            "description": "Example virtual disk",
            "provisioned_size": 10737418240,
            "format": "cow",
            "sparse": True,
            "storage_domains": {
                "storage_domain": [_ref("storagedomains", _SD, name="data1")],
            },
        },
        # Inline disk create — seed disk is already attached to lab-vm-01.
        "disk_attachment": {
            "interface": "virtio_scsi",
            "bootable": False,
            "active": True,
            "disk": {
                "name": "example-attached-disk",
                "provisioned_size": 10737418240,
                "format": "cow",
                "sparse": True,
                "storage_domains": {
                    "storage_domain": [_ref("storagedomains", _SD, name="data1")],
                },
            },
        },
        "nic": {
            "name": "nic1",
            "interface": "virtio",
            "linked": True,
            "plugged": True,
            "vnic_profile": _ref("vnicprofiles", _VNIC, name="ovirtmgmt"),
        },
        "network": {
            "name": "vlan100",
            "description": "Example VLAN network",
            "stp": False,
            "data_center": _ref("datacenters", _DC, name="Default"),
            "vlan": {"id": 100},
        },
        "vnic_profile": {
            "name": "example-profile",
            "pass_through": {"mode": "disabled"},
            "network": _ref("networks", _NET, name="ovirtmgmt"),
        },
        "data_center": {
            "name": "example-dc",
            "description": "Example data center",
            "local": False,
            "version": {"major": 4, "minor": 5},
        },
        "cluster": {
            "name": "example-cluster",
            "description": "Example cluster",
            "data_center": _ref("datacenters", _DC, name="Default"),
            "cpu": {"type": "Intel Conroe Family"},
        },
        "storage_domain": {
            "name": "example-sd",
            "type": "data",
            "storage": {
                "type": "nfs",
                "address": "nfs.lab.local",
                "path": "/export/example",
            },
            "host": _ref("hosts", _HOST, name="host01"),
        },
        "storage_connection": {
            "type": "nfs",
            "address": "nfs.lab.local",
            "path": "/export/example",
        },
        "template": {
            "name": "example-template",
            "description": "Example template",
            "vm": _ref("vms", _VM, name="lab-vm-01"),
            "cluster": _ref("clusters", _CLUSTER, name="Default"),
        },
        "snapshot": {
            "description": "example-snapshot",
            "persist_memorystate": False,
        },
        "tag": {"name": "example-tag", "description": "Example tag"},
        "bookmark": {"name": "example-bookmark", "value": "Vms: status=up"},
        "affinity_group": {
            "name": "example-affinity",
            "description": "Example affinity group",
            "enforcing": False,
            "hosts_rule": {"enabled": True, "positive": True},
            "vms_rule": {"enabled": True, "positive": True},
        },
        "affinity_label": {"name": "example-label"},
        "permission": {
            "role": _ref("roles", _ROLE, name="SuperUser"),
            "user": _ref("users", _USER, name="admin"),
        },
        "user": {
            "user_name": "example@internal",
            "name": "example",
            "domain": _ref("domains", _DOMAIN, name="internal"),
            "password": "secret",
        },
        "group": {"name": "example-group", "domain": _ref("domains", _DOMAIN, name="internal")},
        "role": {"name": "ExampleRole", "administrative": False},
        "quota": {
            "name": "example-quota",
            "description": "Example quota",
            "data_center": _ref("datacenters", _DC, name="Default"),
        },
        "vm_pool": {
            "name": "example-pool",
            "description": "Example VM pool",
            "size": 1,
            "cluster": _ref("clusters", _CLUSTER, name="Default"),
            "template": _ref("templates", _TEMPLATE, name="Blank"),
        },
        "mac_pool": {
            "name": "example-mac-pool",
            "allow_duplicates": False,
            "ranges": {
                "range": [{"from": "00:1A:4A:16:01:00", "to": "00:1A:4A:16:01:FF"}],
            },
        },
        "cdrom": {"file": {"id": ""}},
        "graphics_console": {"protocol": "spice"},
        "host_nic": {
            "name": "eth1",
            "boot_protocol": "none",
            "network": _ref("networks", _NET, name="ovirtmgmt"),
        },
        "scheduling_policy": {"name": "example-policy", "description": "Example policy"},
        "instance_type": {
            "name": "example-instancetype",
            "memory": 1073741824,
            "cpu": {"topology": {"sockets": 1, "cores": 1, "threads": 1}},
        },
        "image_transfer": {
            "disk": _ref("disks", _DISK),
            "direction": "upload",
            "format": "raw",
        },
        "event": {
            "description": "Example event",
            "severity": 1,
            "origin": "ovirt-api-simulator",
        },
        "job": {"description": "Example job"},
        "step": {"description": "Example step", "type": "VALIDATING"},
        "icon": {"media_type": "image/png", "data": ""},
        "file": {"name": "example.iso"},
        "cluster_level": {"id": "4.5"},
        "operating_system": {"name": "other"},
        "domain": {"name": "example.local"},
        "external_host_provider": {
            "name": "example-foreman",
            "url": "https://foreman.example.local",
            "username": "admin",
            "password": "secret",
        },
        "openstack_image_provider": {
            "name": "example-glance",
            "url": "https://glance.example.local:9292",
            "username": "admin",
            "password": "secret",
            "authentication_url": "https://keystone.example.local:5000/v3",
            "tenant_name": "admin",
        },
        "openstack_network_provider": {
            "name": "example-neutron",
            "url": "https://neutron.example.local:9696",
            "username": "admin",
            "password": "secret",
            "authentication_url": "https://keystone.example.local:5000/v3",
            "tenant_name": "admin",
            "plugin_type": "open_vswitch",
            "type": "external",
        },
        "openstack_volume_provider": {
            "name": "example-cinder",
            "url": "https://cinder.example.local:8776/v3",
            "username": "admin",
            "password": "secret",
            "authentication_url": "https://keystone.example.local:5000/v3",
            "tenant_name": "admin",
        },
        "network_filter": {"name": "example-filter"},
        "engine_option": {"name": "ExampleOption", "value": "true"},
        "katello_erratum": {"id": "example-erratum"},
        "statistic": {"name": "example.stat", "type": "GAUGE", "unit": "NONE"},
        "scheduling_policy_unit": {"name": "example-unit", "type": "filter"},
    }


def _action_name(path: str) -> str:
    return path.rstrip("/").rsplit("/", 1)[-1].lower()


def _action_body(path: str) -> dict[str, Any]:
    """Real Engine actions use a root ``action`` element."""

    name = _action_name(path)
    action: dict[str, Any] = {}
    if name == "clone":
        action["vm"] = {"name": "example-vm-clone"}
    elif name == "migrate":
        action["host"] = _ref("hosts", _HOST, name="host01")
    elif name in {"move", "copy"}:
        action["storage_domain"] = _ref("storagedomains", _SD, name="data1")
    elif name == "export":
        action["storage_domain"] = _ref("storagedomains", _SD, name="data1")
        action["exclusive"] = False
    elif name == "import":
        action["cluster"] = _ref("clusters", _CLUSTER, name="Default")
        action["storage_domain"] = _ref("storagedomains", _SD, name="data1")
    elif name == "attach":
        action["disk"] = _ref("disks", _DISK)
    elif name == "detach":
        action["detach_only"] = True
    elif name in {"start", "stop", "shutdown", "reboot", "suspend", "activate", "deactivate"}:
        action["async"] = True
    elif name == "ticket":
        action["ticket"] = {"value": ""}
    elif name == "preview_snapshot":
        action["restore_memory"] = False
    return {"action": action}


def _generic_entity(element: str) -> dict[str, Any]:
    return {
        "name": f"example-{element.replace('_', '-')}",
        "description": f"Example {element.replace('_', ' ')}",
    }


def body_example_for(
    *,
    method: str,
    kind: str,
    element: str,
    path: str,
) -> dict[str, Any] | None:
    """Return a full JSON request body example, or ``None`` when no body is used."""

    method_u = method.upper()
    kind_l = (kind or "").lower()
    element_l = (element or "").strip()
    if method_u not in {"POST", "PUT"}:
        return None
    if kind_l == "action":
        return _action_body(path)
    if kind_l not in {"collection", "item"}:
        return None
    if not element_l:
        return None
    bodies = _entity_bodies()
    inner = dict(bodies.get(element_l) or _generic_entity(element_l))
    if method_u == "PUT":
        # Partial update: avoid renaming path-param seed entities via console Try-it.
        inner.pop("name", None)
        if "description" in inner or element_l not in {"cdrom", "graphics_console", "permission"}:
            inner["description"] = f"Updated {element_l.replace('_', ' ')}"
        if element_l == "vm" and "memory" in inner:
            inner["memory"] = 2147483648
        if element_l == "disk" and "provisioned_size" in inner:
            inner["provisioned_size"] = 21474836480
    return _wrap(element_l, inner)
