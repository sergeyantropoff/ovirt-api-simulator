"""Nested inventory + affinity/quota realism after minimal seed."""

from __future__ import annotations

import uuid

import pytest
import requests

from app.ovirt.ids import stable_id

from .conftest import auth_headers, collection_items, oauth_token

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def session_ctx():
    from .conftest import discover_base_url

    base = discover_base_url()
    token = oauth_token(base)
    return base, auth_headers(token, version="4")


def _ids() -> dict[str, str]:
    return {
        "vm": str(stable_id("vm", "lab-vm-01")),
        "dc": str(stable_id("dc", "Default")),
        "cluster": str(stable_id("cluster", "Default")),
        "host": str(stable_id("host", "host01")),
        "nic": str(stable_id("nic", "lab-vm-01")),
        "snap": str(stable_id("snap", "lab-vm-01", "1")),
        "user": str(stable_id("user", "admin")),
        "net": str(stable_id("net", "ovirtmgmt")),
    }


def test_nested_seeded_collections_non_empty(session_ctx) -> None:
    base, headers = session_ctx
    ids = _ids()
    probes = [
        (f"/ovirt-engine/api/datacenters/{ids['dc']}/quotas", "quota"),
        (f"/ovirt-engine/api/clusters/{ids['cluster']}/affinitygroups", "affinity_group"),
        (f"/ovirt-engine/api/vms/{ids['vm']}/nics", "nic"),
        (f"/ovirt-engine/api/vms/{ids['vm']}/snapshots", "snapshot"),
        (f"/ovirt-engine/api/vms/{ids['vm']}/diskattachments", "disk_attachment"),
        (f"/ovirt-engine/api/vms/{ids['vm']}/graphicsconsoles", "graphics_console"),
        (f"/ovirt-engine/api/vms/{ids['vm']}/mediateddevices", "vm_mediated_device"),
        (f"/ovirt-engine/api/vms/{ids['vm']}/affinitylabels", "affinity_label"),
        (f"/ovirt-engine/api/hosts/{ids['host']}/nics", "nic"),
        (f"/ovirt-engine/api/hosts/{ids['host']}/storage", "host_storage"),
        (f"/ovirt-engine/api/clusters/{ids['cluster']}/glustervolumes", "gluster_volume"),
        (f"/ovirt-engine/api/networks/{ids['net']}/networklabels", "network_label"),
        (f"/ovirt-engine/api/users/{ids['user']}/sshpublickeys", "ssh_public_key"),
        ("/ovirt-engine/api/affinitygroups", "affinity_group"),
        ("/ovirt-engine/api/quotas", "quota"),
    ]
    for path, element in probes:
        r = requests.get(f"{base}{path}", headers=headers, verify=False, timeout=60)
        assert r.status_code == 200, f"{path}: {r.status_code} {r.text[:200]}"
        items = collection_items(r.json(), element)
        assert len(items) >= 1, f"{path}: expected non-empty {element}"
        assert items[0].get("id") and items[0].get("href")


def test_job_steps_and_event_entity_href(session_ctx) -> None:
    base, headers = session_ctx
    jobs = requests.get(f"{base}/ovirt-engine/api/jobs", headers=headers, verify=False, timeout=60)
    assert jobs.status_code == 200
    job = collection_items(jobs.json(), "job")[0]
    steps = requests.get(
        f"{base}/ovirt-engine/api/jobs/{job['id']}/steps",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert steps.status_code == 200
    step = collection_items(steps.json(), "step")[0]
    assert step.get("href") == f"/ovirt-engine/api/jobs/{job['id']}/steps/{step['id']}"
    one = requests.get(
        f"{base}/ovirt-engine/api/jobs/{job['id']}/steps/{step['id']}",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert one.status_code == 200
    assert one.json()["step"]["href"]

    events = requests.get(
        f"{base}/ovirt-engine/api/events", headers=headers, verify=False, timeout=60
    )
    assert events.status_code == 200
    ev = collection_items(events.json(), "event")[0]
    one_ev = requests.get(
        f"{base}/ovirt-engine/api/events/{ev['id']}",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert one_ev.status_code == 200
    assert one_ev.json()["event"].get("href")


def test_vm_tag_and_permission_get_by_id(session_ctx) -> None:
    base, headers = session_ctx
    ids = _ids()
    tags = requests.get(
        f"{base}/ovirt-engine/api/vms/{ids['vm']}/tags",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert tags.status_code == 200
    tag = collection_items(tags.json(), "tag")[0]
    one_tag = requests.get(
        f"{base}/ovirt-engine/api/vms/{ids['vm']}/tags/{tag['id']}",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert one_tag.status_code == 200, one_tag.text
    assert one_tag.json()["tag"]["id"] == tag["id"]

    perms = requests.get(
        f"{base}/ovirt-engine/api/vms/{ids['vm']}/permissions",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert perms.status_code == 200
    perm = collection_items(perms.json(), "permission")[0]
    one_perm = requests.get(
        f"{base}/ovirt-engine/api/vms/{ids['vm']}/permissions/{perm['id']}",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert one_perm.status_code == 200, one_perm.text
    assert one_perm.json()["permission"]["id"] == perm["id"]
    assert one_perm.json()["permission"].get("href")


def test_nic_and_snapshot_get_by_id(session_ctx) -> None:
    base, headers = session_ctx
    ids = _ids()
    nic = requests.get(
        f"{base}/ovirt-engine/api/vms/{ids['vm']}/nics/{ids['nic']}",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert nic.status_code == 200, nic.text
    assert nic.json()["nic"]["id"] == ids["nic"]

    snap = requests.get(
        f"{base}/ovirt-engine/api/vms/{ids['vm']}/snapshots/{ids['snap']}",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert snap.status_code == 200, snap.text
    assert snap.json()["snapshot"]["id"] == ids["snap"]


def test_affinity_group_create_returns_entity(session_ctx) -> None:
    base, headers = session_ctx
    cluster = str(stable_id("cluster", "Default"))
    name = f"ag-{uuid.uuid4().hex[:8]}"
    r = requests.post(
        f"{base}/ovirt-engine/api/clusters/{cluster}/affinitygroups",
        headers=headers,
        json={"affinity_group": {"name": name, "enforcing": False}},
        verify=False,
        timeout=60,
    )
    assert r.status_code == 201, r.text
    body = r.json()["affinity_group"]
    assert body["name"] == name
    assert body["id"] and "/affinitygroups/" in body["href"]

    listing = requests.get(
        f"{base}/ovirt-engine/api/clusters/{cluster}/affinitygroups",
        headers=headers,
        verify=False,
        timeout=60,
    )
    names = [i["name"] for i in collection_items(listing.json(), "affinity_group")]
    assert name in names


def test_quota_create_and_read_after_write(session_ctx) -> None:
    base, headers = session_ctx
    dc = str(stable_id("dc", "Default"))
    name = f"quota-{uuid.uuid4().hex[:8]}"
    created = requests.post(
        f"{base}/ovirt-engine/api/datacenters/{dc}/quotas",
        headers=headers,
        json={"quota": {"name": name, "description": "lab"}},
        verify=False,
        timeout=60,
    )
    assert created.status_code == 201, created.text
    qid = created.json()["quota"]["id"]
    detail = requests.get(
        f"{base}/ovirt-engine/api/datacenters/{dc}/quotas/{qid}",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert detail.status_code == 200
    assert detail.json()["quota"]["name"] == name


def test_template_create_from_vm_copies_nested(session_ctx) -> None:
    base, headers = session_ctx
    vm = str(stable_id("vm", "lab-vm-01"))
    name = f"tpl-{uuid.uuid4().hex[:8]}"
    created = requests.post(
        f"{base}/ovirt-engine/api/templates",
        headers=headers,
        json={"template": {"name": name, "vm": {"id": vm}}},
        verify=False,
        timeout=60,
    )
    assert created.status_code == 201, created.text
    tid = created.json()["template"]["id"]
    nics = requests.get(
        f"{base}/ovirt-engine/api/templates/{tid}/nics",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert nics.status_code == 200
    assert len(collection_items(nics.json(), "nic")) >= 1
    das = requests.get(
        f"{base}/ovirt-engine/api/templates/{tid}/diskattachments",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert das.status_code == 200
    assert len(collection_items(das.json(), "disk_attachment")) >= 1


def test_vm_clone_copies_nics_and_disks(session_ctx) -> None:
    base, headers = session_ctx
    vm = str(stable_id("vm", "lab-vm-01"))
    clone_name = f"clone-{uuid.uuid4().hex[:8]}"
    action = requests.post(
        f"{base}/ovirt-engine/api/vms/{vm}/clone",
        headers=headers,
        json={"action": {"vm": {"name": clone_name}}},
        verify=False,
        timeout=60,
    )
    assert action.status_code == 200, action.text
    assert "job" in action.json().get("action", {})

    listing = requests.get(
        f"{base}/ovirt-engine/api/vms",
        headers=headers,
        verify=False,
        timeout=60,
    )
    vms = {v["name"]: v for v in collection_items(listing.json(), "vm")}
    assert clone_name in vms
    clone_id = vms[clone_name]["id"]
    nics = requests.get(
        f"{base}/ovirt-engine/api/vms/{clone_id}/nics",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert len(collection_items(nics.json(), "nic")) >= 1
    das = requests.get(
        f"{base}/ovirt-engine/api/vms/{clone_id}/diskattachments",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert len(collection_items(das.json(), "disk_attachment")) >= 1
