"""Surface probe: GET/POST/PUT/DELETE happy paths across Engine collections."""

from __future__ import annotations

import uuid

import pytest
import requests

from .conftest import auth_headers, collection_items, discover_base_url, oauth_token

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def session_ctx():
    base = discover_base_url()
    token = oauth_token(base)
    return base, auth_headers(token, version="4")


def test_get_all_top_level_collections(session_ctx) -> None:
    base, headers = session_ctx
    collections = {
        "datacenters": "data_center",
        "clusters": "cluster",
        "hosts": "host",
        "vms": "vm",
        "disks": "disk",
        "networks": "network",
        "vnicprofiles": "vnic_profile",
        "storagedomains": "storage_domain",
        "storageconnections": "storage_connection",
        "templates": "template",
        "users": "user",
        "groups": "group",
        "roles": "role",
        "events": "event",
        "jobs": "job",
        "tags": "tag",
        "bookmarks": "bookmark",
        "instancetypes": "instance_type",
        "macpools": "mac_pool",
        "schedulingpolicies": "scheduling_policy",
        "schedulingpolicyunits": "scheduling_policy_unit",
        "clusterlevels": "cluster_level",
        "icons": "icon",
        "operatingsystems": "operating_system",
        "networkfilters": "network_filter",
        "vmpools": "vm_pool",
        "affinitylabels": "affinity_label",
        "permissions": "permission",
        "domains": "domain",
        "options": "engine_option",
        "imagetransfers": "image_transfer",
        "katelloerrata": "katello_erratum",
        "externalhostproviders": "external_host_provider",
        "openstacknetworkproviders": "openstack_network_provider",
        "openstackimageproviders": "openstack_image_provider",
        "openstackvolumeproviders": "openstack_volume_provider",
    }
    for name, element in collections.items():
        r = requests.get(f"{base}/ovirt-engine/api/{name}", headers=headers, verify=False, timeout=60)
        assert r.status_code == 200, f"{name}: {r.status_code} {r.text[:200]}"
        items = collection_items(r.json(), element)
        assert len(items) >= 1, f"{name}: expected seeded rows, got empty"


def test_host_activate_deactivate(session_ctx) -> None:
    base, headers = session_ctx
    hosts = requests.get(f"{base}/ovirt-engine/api/hosts", headers=headers, verify=False, timeout=60)
    host = hosts.json()["host"]
    hid = host[0]["id"] if isinstance(host, list) else host["id"]
    for action in ("deactivate", "activate"):
        r = requests.post(
            f"{base}/ovirt-engine/api/hosts/{hid}/{action}",
            headers=headers,
            json={"action": {}},
            verify=False,
            timeout=60,
        )
        assert r.status_code == 200, action


def test_tags_bookmarks_crud(session_ctx) -> None:
    base, headers = session_ctx
    name = f"tag-{uuid.uuid4().hex[:8]}"
    create = requests.post(
        f"{base}/ovirt-engine/api/tags",
        headers=headers,
        json={"tag": {"name": name, "description": "t"}},
        verify=False,
        timeout=60,
    )
    assert create.status_code == 201, create.text
    tid = create.json()["tag"]["id"]
    got = requests.get(f"{base}/ovirt-engine/api/tags/{tid}", headers=headers, verify=False, timeout=60)
    assert got.status_code == 200
    delete = requests.delete(
        f"{base}/ovirt-engine/api/tags/{tid}", headers=headers, verify=False, timeout=60
    )
    assert delete.status_code == 200

    bname = f"bm-{uuid.uuid4().hex[:6]}"
    bc = requests.post(
        f"{base}/ovirt-engine/api/bookmarks",
        headers=headers,
        json={"bookmark": {"name": bname, "value": "Vms:"}},
        verify=False,
        timeout=60,
    )
    assert bc.status_code == 201
    bid = bc.json()["bookmark"]["id"]
    requests.delete(f"{base}/ovirt-engine/api/bookmarks/{bid}", headers=headers, verify=False, timeout=60)


def test_snapshot_flow(session_ctx) -> None:
    base, headers = session_ctx
    clusters = requests.get(f"{base}/ovirt-engine/api/clusters", headers=headers, verify=False, timeout=60)
    cluster = clusters.json()["cluster"]
    cid = cluster[0]["id"] if isinstance(cluster, list) else cluster["id"]
    vm = requests.post(
        f"{base}/ovirt-engine/api/vms",
        headers=headers,
        json={"vm": {"name": f"snap-{uuid.uuid4().hex[:6]}", "cluster": {"id": cid}}},
        verify=False,
        timeout=60,
    ).json()["vm"]
    snap = requests.post(
        f"{base}/ovirt-engine/api/vms/{vm['id']}/snapshots",
        headers=headers,
        json={"snapshot": {"description": "s1"}},
        verify=False,
        timeout=60,
    )
    assert snap.status_code == 201
    sid = snap.json()["snapshot"]["id"]
    lst = requests.get(
        f"{base}/ovirt-engine/api/vms/{vm['id']}/snapshots",
        headers=headers,
        verify=False,
        timeout=60,
    )
    assert lst.status_code == 200
    requests.delete(
        f"{base}/ovirt-engine/api/vms/{vm['id']}/snapshots/{sid}",
        headers=headers,
        verify=False,
        timeout=60,
    )
    requests.delete(f"{base}/ovirt-engine/api/vms/{vm['id']}", headers=headers, verify=False, timeout=60)
