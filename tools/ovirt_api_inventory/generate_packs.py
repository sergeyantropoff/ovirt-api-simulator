#!/usr/bin/env python3
"""Generate contracts/ovirt/<series>/ packs from the master catalog."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ovirt_api_inventory.catalog import (  # noqa: E402
    SERIES,
    SERIES_MAJOR,
    SERIES_PRODUCT,
    api_version_for_series,
    build_operations,
    entry_point_links,
)


def emit_series(series: str, out_root: Path) -> dict:
    ops = build_operations(series)
    series_dir = out_root / series
    series_dir.mkdir(parents=True, exist_ok=True)
    api_ver = api_version_for_series(series)
    product = SERIES_PRODUCT[series]

    operations = [
        {
            "operation_id": op.operation_id,
            "method": op.method,
            "path": op.path,
            "resource_type": op.resource_type,
            "collection_key": op.collection_key,
            "element": op.element,
            "kind": op.kind,
            "search": op.search,
            "introduced_in": op.introduced_in,
            "requires_auth": op.kind != "root",
            "status_code": 200 if op.method != "POST" or op.kind == "action" else 201,
            "create_status": 201,
            "notes": op.notes,
        }
        for op in ops
    ]

    payload = {
        "service": "engine",
        "type": "ovirt-engine",
        "api_version": api_ver,
        "series": series,
        "product": product,
        "operations": operations,
    }
    api_path = series_dir / "api.json"
    raw = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    api_path.write_text(raw)
    checksum = hashlib.sha256(raw.encode()).hexdigest()

    # Series deltas vs previous
    idx = SERIES.index(series)
    prev_ops = set()
    if idx > 0:
        prev = build_operations(SERIES[idx - 1])
        prev_ops = {(o.method, o.path) for o in prev}
    cur_ops = {(o.method, o.path) for o in ops}
    added = sorted(f"{m} {p}" for m, p in (cur_ops - prev_ops))
    removed = sorted(f"{m} {p}" for m, p in (prev_ops - cur_ops))

    deltas = {
        "series": series,
        "previous": SERIES[idx - 1] if idx > 0 else None,
        "added_count": len(added),
        "removed_count": len(removed),
        "added": added[:200],
        "removed": removed[:200],
    }
    (series_dir / "deltas.json").write_text(json.dumps(deltas, indent=2) + "\n")

    manifest = {
        "series": series,
        "major": SERIES_MAJOR[series],
        "api_version": api_ver,
        "product": product,
        "operation_count": len(operations),
        "service_count": 1,
        "services": ["engine"],
        "checksum": checksum,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entry_point_links": entry_point_links(series),
        "deltas": {"added": deltas["added_count"], "removed": deltas["removed_count"]},
    }
    (series_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> int:
    out = ROOT / "contracts" / "ovirt"
    out.mkdir(parents=True, exist_ok=True)
    summaries = []
    for series in SERIES:
        man = emit_series(series, out)
        summaries.append(man)
        print(f"{series}: {man['operation_count']} ops (api v{man['api_version']})")
    index = {
        "series": summaries,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (out / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
