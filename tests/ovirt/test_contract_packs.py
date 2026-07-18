"""Contract pack integrity and series deltas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ovirt.contract_loader import list_series, load_series_pack, major_for_series
from tools.ovirt_api_inventory.catalog import SERIES

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts" / "ovirt"


@pytest.mark.contract
def test_all_series_packs_exist() -> None:
    available = {s["series"] for s in list_series()}
    for series in SERIES:
        assert series in available
        pack = load_series_pack(series)
        assert pack.operation_count() > 0
        assert pack.api_version in {"3", "4"}


@pytest.mark.contract
def test_series_deltas_are_real() -> None:
    """Later series must not be identical copies of earlier inventories."""

    counts = []
    for series in SERIES:
        man = json.loads((CONTRACTS / series / "manifest.json").read_text())
        counts.append((series, man["operation_count"]))
    # 3.0 < 3.3 < 4.3 (real growth)
    by = dict(counts)
    assert by["3.0"] < by["3.3"]
    assert by["3.3"] < by["4.3"]
    assert by["4.3"] <= by["4.5"]
    # deltas files record added ops
    d33 = json.loads((CONTRACTS / "3.3" / "deltas.json").read_text())
    assert d33["added_count"] > 0
    assert any("vnicprofiles" in x for x in d33["added"])


@pytest.mark.contract
def test_v3_vs_v4_api_version() -> None:
    assert load_series_pack("3.6").api_version == "3"
    assert load_series_pack("4.5").api_version == "4"
    assert major_for_series("4.5") == 45


@pytest.mark.contract
def test_entry_point_links_grow() -> None:
    early = json.loads((CONTRACTS / "3.0" / "manifest.json").read_text())
    late = json.loads((CONTRACTS / "4.5" / "manifest.json").read_text())
    early_rels = {l["rel"] for l in early["entry_point_links"]}
    late_rels = {l["rel"] for l in late["entry_point_links"]}
    assert "vms" in early_rels
    assert "vnicprofiles" in late_rels
    assert "vnicprofiles" not in early_rels or "affinitylabels" in late_rels - early_rels
