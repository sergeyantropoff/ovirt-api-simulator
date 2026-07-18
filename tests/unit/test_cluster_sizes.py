"""Cluster size specs for demo seed profiles."""

from __future__ import annotations

import pytest

from app.ovirt.demo_datacenter import CLUSTER_SIZES, normalize_cluster_size


@pytest.mark.parametrize(
    ("name", "hosts", "vms"),
    [
        ("small", 3, 50),
        ("large", 10, 1000),
        ("big", 30, 2000),
    ],
)
def test_cluster_size_targets(name: str, hosts: int, vms: int) -> None:
    spec = CLUSTER_SIZES[name]
    assert spec.hosts == hosts
    assert spec.vms == vms
    topology = spec.datacenters * spec.clusters_per_dc * spec.hosts_per_cluster
    assert topology == hosts


def test_demo_alias_maps_to_large() -> None:
    assert normalize_cluster_size("demo") == "large"
    assert normalize_cluster_size("LARGE") == "large"


def test_unknown_size_raises() -> None:
    with pytest.raises(ValueError):
        normalize_cluster_size("huge")
