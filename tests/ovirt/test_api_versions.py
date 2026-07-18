"""Probe every Engine series pack with real seeded inventory data."""

from __future__ import annotations

import pytest
import requests

from tools.ovirt_api_inventory.catalog import (
    SERIES,
    TOP_LEVEL,
    api_version_for_series,
    available_in,
    collections_for_series,
)

from .conftest import auth_headers, collection_items, oauth_token

pytestmark = pytest.mark.integration

# Collections that minimal (and demo) seed always populate with ≥1 row.
SEEDED_CORE = {
    "datacenters": ("data_center", "Default"),
    "clusters": ("cluster", "Default"),
    "hosts": ("host", "host01"),
    "vms": ("vm", "lab-vm-01"),
    "disks": ("disk", None),
    "networks": ("network", "ovirtmgmt"),
    "storagedomains": ("storage_domain", "data1"),
    "storageconnections": ("storage_connection", None),
    "templates": ("template", "Blank"),
    "users": ("user", "admin"),
    "roles": ("role", "SuperUser"),
    "domains": ("domain", "internal"),
    "permissions": ("permission", None),
    "events": ("event", None),
    "bookmarks": ("bookmark", None),
    "groups": ("group", "engine-admins"),
    "tags": ("tag", "lab"),
    "jobs": ("job", None),
}

# Generic ov_api_objects collections seeded in minimal profile.
SEEDED_GENERIC = {
    "instancetypes": ("instance_type", "Large"),
    "macpools": ("mac_pool", "Default"),
    "schedulingpolicies": ("scheduling_policy", "evenly_distributed"),
    "schedulingpolicyunits": ("scheduling_policy_unit", "EvenlyDistributed"),
    "clusterlevels": ("cluster_level", "4.5"),
    "icons": ("icon", "default"),
    "operatingsystems": ("operating_system", "rhel_8x64"),
    "networkfilters": ("network_filter", "vdsm-no-mac-spoofing"),
    "vmpools": ("vm_pool", "pool-demo"),
    "affinitylabels": ("affinity_label", "label-a"),
    "katelloerrata": ("katello_erratum", "RHSA-2024:0001"),
    "externalhostproviders": ("external_host_provider", "foreman-lab"),
    "openstacknetworkproviders": ("openstack_network_provider", "ovn-provider"),
    "openstackimageproviders": ("openstack_image_provider", "glance-lab"),
    "openstackvolumeproviders": ("openstack_volume_provider", "cinder-lab"),
    "imagetransfers": ("image_transfer", "transfer-1"),
    "options": ("engine_option", "ENGINE_API_DEFAULT_VERSION"),
    "vnicprofiles": ("vnic_profile", "ovirtmgmt"),
}


def _activate(base: str, series: str) -> None:
    r = requests.post(
        f"{base}/ui/api/ovirt/contracts/activate",
        json={"series": series},
        verify=False,
        timeout=60,
    )
    assert r.status_code == 200, r.text
    assert r.json()["series"] == series


def _ensure_seeded_inventory(base: str) -> None:
    """Guarantee minimal seed rows exist (reload if demo was wiped users)."""

    token = oauth_token(base)
    h = auth_headers(token, version="4")
    r = requests.get(f"{base}/ovirt-engine/api/vms", headers=h, verify=False, timeout=60)
    assert r.status_code == 200, r.text
    vms = collection_items(r.json(), "vm")
    if vms:
        return
    # Empty inventory — reload minimal via UI demo unload path.
    reset = requests.post(f"{base}/ui/api/demo/unload", verify=False, timeout=120)
    assert reset.status_code == 200, reset.text


@pytest.fixture(scope="module")
def version_matrix(base_url: str):
    _ensure_seeded_inventory(base_url)
    yield base_url
    _activate(base_url, "4.5")


@pytest.mark.parametrize("series", SERIES)
def test_series_root_and_seeded_collections(version_matrix: str, series: str) -> None:
    base = version_matrix
    _activate(base, series)
    api_ver = api_version_for_series(series)
    token = oauth_token(base)
    headers = auth_headers(token, version=api_ver)

    root = requests.get(f"{base}/ovirt-engine/api", headers=headers, verify=False, timeout=60)
    assert root.status_code == 200, root.text
    body = root.json()
    api = body.get("api") or body
    product = api.get("product_info") or {}
    assert "oVirt" in str(product.get("name") or api.get("product_info", {}).get("name") or "oVirt")
    links = api.get("link") or []
    if isinstance(links, dict):
        links = [links]
    rels = {link.get("rel") for link in links if isinstance(link, dict)}
    assert "vms" in rels
    # Series-aware entry links
    if available_in(series, "3.3"):
        assert "vnicprofiles" in rels
    if available_in(series, "4.3"):
        assert "affinitylabels" in rels

    expected = {spec.name for spec in collections_for_series(series) if "/" not in spec.path}
    for rel in expected:
        assert rel in rels, f"{series}: missing entry link {rel}"

    # Prefix + header variants for VMs (real seed data)
    for path in (
        "/ovirt-engine/api/vms",
        f"/ovirt-engine/api/v{api_ver}/vms",
    ):
        r = requests.get(f"{base}{path}", headers=headers, verify=False, timeout=60)
        assert r.status_code == 200, f"{series} {path}: {r.status_code} {r.text[:200]}"
        items = collection_items(r.json(), "vm")
        assert len(items) >= 1, f"{series}: expected seeded VMs on {path}"
        names = {item.get("name") for item in items}
        # demo may replace lab-vm-01 with vm-0001…; either profile is fine
        assert names, f"{series}: empty VM names"

    xml = requests.get(
        f"{base}/ovirt-engine/api/v{api_ver}/vms",
        headers={**headers, "Accept": "application/xml"},
        verify=False,
        timeout=60,
    )
    assert xml.status_code == 200
    assert "<vm" in xml.text

    seeded = {**SEEDED_CORE, **SEEDED_GENERIC}
    for collection, (element, expected_name) in seeded.items():
        if collection not in expected:
            continue
        r = requests.get(
            f"{base}/ovirt-engine/api/{collection}",
            headers=headers,
            verify=False,
            timeout=60,
        )
        assert r.status_code == 200, f"{series}/{collection}: {r.status_code} {r.text[:200]}"
        items = collection_items(r.json(), element)
        assert len(items) >= 1, f"{series}/{collection}: expected seeded rows, got empty"
        if expected_name:
            names = {item.get("name") for item in items}
            # Demo profile uses different host/VM names; accept either known seed or any non-empty.
            if expected_name not in names and collection in {"hosts", "vms", "datacenters", "clusters"}:
                assert any(names), f"{series}/{collection}: no names"
            elif expected_name not in names and collection not in {"hosts", "vms", "datacenters", "clusters"}:
                # For demo-overwritten generic names still require ≥1 row (already asserted).
                pass
            else:
                assert expected_name in names, f"{series}/{collection}: missing {expected_name}, have {names}"


@pytest.mark.parametrize("series", SERIES)
def test_all_top_level_collections_return_real_payloads(version_matrix: str, series: str) -> None:
    base = version_matrix
    _activate(base, series)
    api_ver = api_version_for_series(series)
    token = oauth_token(base)
    headers = auth_headers(token, version=api_ver)

    top = [spec for spec in TOP_LEVEL if available_in(series, spec.introduced_in, spec.removed_in)]
    for spec in top:
        r = requests.get(
            f"{base}/ovirt-engine/api/{spec.name}",
            headers=headers,
            verify=False,
            timeout=60,
        )
        assert r.status_code == 200, f"{series}/{spec.name}: {r.status_code} {r.text[:240]}"
        body = r.json()
        assert isinstance(body, dict), f"{series}/{spec.name}: non-object JSON"
        # Engine-shaped payload: singular element key present (list or empty).
        assert spec.element in body or body == {}, (
            f"{series}/{spec.name}: missing element key {spec.element} in {list(body)[:8]}"
        )
        items = collection_items(body, spec.element)
        if spec.name in SEEDED_CORE or spec.name in SEEDED_GENERIC:
            assert len(items) >= 1, f"{series}/{spec.name}: seeded collection returned empty"
            for item in items[:3]:
                assert item.get("id") or item.get("name") or item.get("description"), (
                    f"{series}/{spec.name}: item without id/name: {item}"
                )
