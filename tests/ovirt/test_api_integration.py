"""Integration tests against the running Compose Engine gateway + PostgreSQL."""

from __future__ import annotations

import base64

import pytest
import requests

from .conftest import collection_items, oauth_token

pytestmark = pytest.mark.integration


def test_oauth_and_basic_auth(base_url: str) -> None:
    token = oauth_token(base_url)
    r = requests.get(
        f"{base_url}/ovirt-engine/api",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json", "Version": "4"},
        verify=False,
        timeout=60,
    )
    assert r.status_code == 200
    body = r.json()
    assert "api" in body or "product_info" in body

    basic = base64.b64encode(b"admin@internal:secret").decode()
    r2 = requests.get(
        f"{base_url}/ovirt-engine/api/vms",
        headers={"Authorization": f"Basic {basic}", "Accept": "application/json"},
        verify=False,
        timeout=60,
    )
    assert r2.status_code == 200
    assert len(collection_items(r2.json(), "vm")) >= 1


def test_vm_lifecycle_and_disk(base_url: str) -> None:
    token = oauth_token(base_url)
    h = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    clusters = requests.get(f"{base_url}/ovirt-engine/api/clusters", headers=h, verify=False, timeout=60)
    assert clusters.status_code == 200
    cluster = clusters.json()["cluster"]
    cluster_id = cluster[0]["id"] if isinstance(cluster, list) else cluster["id"]

    create = requests.post(
        f"{base_url}/ovirt-engine/api/vms",
        headers=h,
        json={"vm": {"name": "itest-vm-1", "cluster": {"id": cluster_id}, "memory": 1073741824}},
        verify=False,
        timeout=60,
    )
    assert create.status_code == 201, create.text
    vm_id = create.json()["vm"]["id"]

    upd = requests.put(
        f"{base_url}/ovirt-engine/api/vms/{vm_id}",
        headers=h,
        json={"vm": {"name": "itest-vm-1b", "memory": 2147483648}},
        verify=False,
        timeout=60,
    )
    assert upd.status_code == 200
    assert upd.json()["vm"]["name"] == "itest-vm-1b"

    start = requests.post(
        f"{base_url}/ovirt-engine/api/vms/{vm_id}/start",
        headers=h,
        json={"action": {}},
        verify=False,
        timeout=60,
    )
    assert start.status_code == 200

    disk = requests.post(
        f"{base_url}/ovirt-engine/api/disks",
        headers=h,
        json={"disk": {"name": "itest-disk", "provisioned_size": 10737418240}},
        verify=False,
        timeout=60,
    )
    assert disk.status_code == 201, disk.text
    disk_id = disk.json()["disk"]["id"]

    expand = requests.put(
        f"{base_url}/ovirt-engine/api/disks/{disk_id}",
        headers=h,
        json={"disk": {"provisioned_size": 21474836480}},
        verify=False,
        timeout=60,
    )
    assert expand.status_code == 200

    attach = requests.post(
        f"{base_url}/ovirt-engine/api/vms/{vm_id}/diskattachments",
        headers=h,
        json={"disk_attachment": {"disk": {"id": disk_id}, "interface": "virtio_scsi"}},
        verify=False,
        timeout=60,
    )
    assert attach.status_code == 201

    nic = requests.post(
        f"{base_url}/ovirt-engine/api/vms/{vm_id}/nics",
        headers=h,
        json={"nic": {"name": "nic1", "interface": "virtio"}},
        verify=False,
        timeout=60,
    )
    assert nic.status_code == 201

    stop = requests.post(
        f"{base_url}/ovirt-engine/api/vms/{vm_id}/stop",
        headers=h,
        json={"action": {}},
        verify=False,
        timeout=60,
    )
    assert stop.status_code == 200

    requests.delete(f"{base_url}/ovirt-engine/api/disks/{disk_id}", headers=h, verify=False, timeout=60)
    delete = requests.delete(
        f"{base_url}/ovirt-engine/api/vms/{vm_id}", headers=h, verify=False, timeout=60
    )
    assert delete.status_code == 200


def test_inventory_collections(base_url: str) -> None:
    token = oauth_token(base_url)
    h = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    expected = {
        "/ovirt-engine/api/datacenters": "data_center",
        "/ovirt-engine/api/clusters": "cluster",
        "/ovirt-engine/api/hosts": "host",
        "/ovirt-engine/api/storagedomains": "storage_domain",
        "/ovirt-engine/api/networks": "network",
        "/ovirt-engine/api/vnicprofiles": "vnic_profile",
        "/ovirt-engine/api/templates": "template",
        "/ovirt-engine/api/users": "user",
        "/ovirt-engine/api/roles": "role",
        "/ovirt-engine/api/domains": "domain",
        "/ovirt-engine/api/permissions": "permission",
        "/ovirt-engine/api/events": "event",
        "/ovirt-engine/api/jobs": "job",
        "/ovirt-engine/api/tags": "tag",
        "/ovirt-engine/api/bookmarks": "bookmark",
        "/ovirt-engine/api/groups": "group",
        "/ovirt-engine/api/instancetypes": "instance_type",
        "/ovirt-engine/api/macpools": "mac_pool",
        "/ovirt-engine/api/schedulingpolicies": "scheduling_policy",
    }
    for path, element in expected.items():
        r = requests.get(f"{base_url}{path}", headers=h, verify=False, timeout=60)
        assert r.status_code == 200, path
        assert len(collection_items(r.json(), element)) >= 1, f"{path} empty"


def test_xml_accept_and_v4_prefix(base_url: str) -> None:
    token = oauth_token(base_url)
    r = requests.get(
        f"{base_url}/ovirt-engine/api/v4/vms",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/xml"},
        verify=False,
        timeout=60,
    )
    assert r.status_code == 200
    assert "<vms" in r.text or "<vm" in r.text


def test_series_hot_swap(base_url: str) -> None:
    r = requests.post(
        f"{base_url}/ui/api/ovirt/contracts/activate",
        json={"series": "3.6"},
        verify=False,
        timeout=60,
    )
    assert r.status_code == 200
    assert r.json()["series"] == "3.6"
    token = oauth_token(base_url)
    vms = requests.get(
        f"{base_url}/ovirt-engine/api/v3/vms",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Version": "3",
        },
        verify=False,
        timeout=60,
    )
    assert vms.status_code == 200
    assert len(collection_items(vms.json(), "vm")) >= 1
    r2 = requests.post(
        f"{base_url}/ui/api/ovirt/contracts/activate",
        json={"series": "4.5"},
        verify=False,
        timeout=60,
    )
    assert r2.status_code == 200
