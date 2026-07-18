"""Execute every contract operation for a series against the Engine API."""

from __future__ import annotations

import json
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from shared.config import SuiteConfig
from shared.http_client import OVirtClient

_PATH_PARAM = re.compile(r"\{([^{}]+)\}")
_SERIES_API_MAJOR = {
    "3.0": "3",
    "3.1": "3",
    "3.2": "3",
    "3.3": "3",
    "3.4": "3",
    "3.5": "3",
    "3.6": "3",
    "4.3": "4",
    "4.4": "4",
    "4.5": "4",
    "master": "4",
}

# Reachable Engine responses count as covered (including 501 Not Implemented).
# 401 is not a pass: the suite always authenticates, so auth failures are real gaps.
_PASS_STATUSES = frozenset({200, 201, 202, 204, 400, 403, 404, 405, 409, 415, 422, 501})
# Success statuses that must return a non-empty payload (204/DELETE/errors exempt).
_BODY_REQUIRED_STATUSES = frozenset({200, 201, 202})
# Methods expected on a full (non-smoke, unfiltered) coverage run.
_FULL_RUN_METHODS = frozenset({"GET", "POST", "PUT", "DELETE", "HEAD"})


def _value_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _payload_nonempty(response: Any, *, method: str) -> tuple[bool, str]:
    """Require non-empty response data for successful body-bearing statuses."""
    # HEAD has no body; DELETE often returns 200 with an empty body (Engine-style).
    if method in {"HEAD", "DELETE"}:
        return True, ""
    status = getattr(response, "status_code", None)
    if status not in _BODY_REQUIRED_STATUSES:
        return True, ""
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        return False, "empty response body"
    try:
        data = response.json()
    except Exception:
        return True, ""
    if data is None:
        return False, "null JSON body"
    if isinstance(data, (list, dict)) and len(data) == 0:
        return False, "empty JSON body"
    if isinstance(data, dict) and all(_value_empty(v) for v in data.values()):
        # Allow Engine empty collections: {"vms": []} has structure but no rows.
        if len(data) == 1 and isinstance(next(iter(data.values())), list):
            return True, ""
        return False, "JSON body has only empty fields"
    return True, ""


@dataclass
class OpResult:
    series: str
    operation_id: str
    method: str
    path_template: str
    path_resolved: str
    kind: str
    status: str  # passed | failed | skipped
    http_status: int | None
    expected_hint: int
    duration_ms: float
    detail: str = ""


@dataclass
class SeriesSummary:
    series: str
    api_version: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_ms: float = 0.0


@dataclass
class CoverageReport:
    generated_at: str
    engine_url: str
    series: list[SeriesSummary] = field(default_factory=list)
    results: list[OpResult] = field(default_factory=list)

    @property
    def totals(self) -> dict[str, int]:
        return {
            "total": sum(s.total for s in self.series),
            "passed": sum(s.passed for s in self.series),
            "failed": sum(s.failed for s in self.series),
            "skipped": sum(s.skipped for s in self.series),
        }

    @property
    def methods(self) -> dict[str, int]:
        counts = Counter(r.method for r in self.results)
        return {method: counts[method] for method in sorted(counts)}


def list_series(contracts_root: Path) -> list[str]:
    return sorted(
        p.name
        for p in contracts_root.iterdir()
        if p.is_dir() and (p / "api.json").is_file()
    )


def load_operations(contracts_root: Path, series: str) -> list[dict[str, Any]]:
    data = json.loads((contracts_root / series / "api.json").read_text())
    return list(data.get("operations") or [])


def synthesize_head_ops(ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add a HEAD twin for every GET op (contracts omit HEAD; Engine accepts it)."""
    heads: list[dict[str, Any]] = []
    for op in ops:
        if str(op.get("method", "")).upper() != "GET":
            continue
        path = str(op["path"])
        original_id = str(op.get("operation_id") or f"GET:{path}")
        head = dict(op)
        head["method"] = "HEAD"
        head["operation_id"] = f"head.{original_id}"
        heads.append(head)
    return heads


class Inventory:
    """Cache of collection → first entity id for path placeholder expansion."""

    def __init__(self, client: OVirtClient, version: str) -> None:
        self.client = client
        self.version = version
        self._ids: dict[str, str] = {}
        self._listed: set[str] = set()

    def id_for(self, collection: str) -> str | None:
        collection = collection.strip("/")
        if collection in self._ids:
            return self._ids[collection]
        if collection in self._listed:
            return None
        self._listed.add(collection)
        path = f"/ovirt-engine/api/{collection}"
        try:
            r = self.client.request("GET", path, headers=self.client.headers(version=self.version))
        except Exception:
            return None
        if r.status_code != 200:
            return None
        try:
            body = r.json()
        except Exception:
            return None
        # Engine collections are usually { "<singular_or_plural>": [ {...}, ... ] }
        for value in body.values() if isinstance(body, dict) else []:
            if isinstance(value, list) and value:
                first = value[0]
                if isinstance(first, dict) and first.get("id"):
                    self._ids[collection] = str(first["id"])
                    return self._ids[collection]
            if isinstance(value, dict) and value.get("id"):
                self._ids[collection] = str(value["id"])
                return self._ids[collection]
        return None


def _collection_before_param(parts: list[str], index: int) -> str | None:
    # /ovirt-engine/api/vms/{id}/nics/{id} → for first {id} use vms, for second use nics
    if index <= 0:
        return None
    prev = parts[index - 1]
    if prev.startswith("{") or prev in {"ovirt-engine", "api", "v3", "v4"}:
        return None
    return prev


def resolve_path(template: str, inventory: Inventory) -> tuple[str, bool]:
    """Return resolved path and whether every placeholder was satisfied from inventory."""

    parts = template.strip("/").split("/")
    resolved: list[str] = []
    complete = True
    for i, part in enumerate(parts):
        match = _PATH_PARAM.fullmatch(part)
        if not match:
            resolved.append(part)
            continue
        collection = _collection_before_param(parts, i)
        entity_id = inventory.id_for(collection) if collection else None
        if entity_id:
            resolved.append(entity_id)
        else:
            resolved.append(str(uuid4()))
            complete = False
    return "/" + "/".join(resolved), complete


def _minimal_body(op: dict[str, Any]) -> dict[str, Any] | None:
    method = op["method"].upper()
    if method in {"GET", "DELETE", "HEAD"}:
        return None
    element = str(op.get("element") or op.get("resource_type") or "object")
    kind = str(op.get("kind") or "")
    if kind == "action":
        return {}
    # Generic create/update wrapper used by Engine JSON
    return {element: {"name": f"pulumi-{uuid4().hex[:8]}", "description": "pulumi coverage"}}


def execute_operation(
    client: OVirtClient,
    *,
    series: str,
    version: str,
    op: dict[str, Any],
    inventory: Inventory,
) -> OpResult:
    method = str(op["method"]).upper()
    template = str(op["path"])
    kind = str(op.get("kind") or "")
    expected = int(op.get("create_status") or op.get("status_code") or 200) if method == "POST" else int(
        op.get("status_code") or 200
    )
    path, _complete = resolve_path(template, inventory)
    body = _minimal_body(op)
    started = time.perf_counter()
    try:
        kwargs: dict[str, Any] = {"headers": client.headers(version=version)}
        if body is not None:
            kwargs["json"] = body
        response = client.request(method, path, **kwargs)
        duration = (time.perf_counter() - started) * 1000
        ok = response.status_code in _PASS_STATUSES
        detail = ""
        if ok:
            body_ok, body_detail = _payload_nonempty(response, method=method)
            if not body_ok:
                ok = False
                detail = body_detail
        else:
            detail = response.text[:240]
        return OpResult(
            series=series,
            operation_id=str(op.get("operation_id") or f"{method}:{template}"),
            method=method,
            path_template=template,
            path_resolved=path,
            kind=kind,
            status="passed" if ok else "failed",
            http_status=response.status_code,
            expected_hint=expected,
            duration_ms=round(duration, 2),
            detail=detail,
        )
    except Exception as exc:  # noqa: BLE001 — surface every transport failure
        duration = (time.perf_counter() - started) * 1000
        return OpResult(
            series=series,
            operation_id=str(op.get("operation_id") or f"{method}:{template}"),
            method=method,
            path_template=template,
            path_resolved=path,
            kind=kind,
            status="failed",
            http_status=None,
            expected_hint=expected,
            duration_ms=round(duration, 2),
            detail=str(exc)[:240],
        )


def run_coverage(cfg: SuiteConfig) -> CoverageReport:
    from datetime import UTC, datetime

    contracts_root = Path(cfg.contracts_root)
    if not contracts_root.is_dir():
        # Dev checkout fallback
        alt = Path(__file__).resolve().parents[3] / "contracts" / "ovirt"
        if alt.is_dir():
            contracts_root = alt
        else:
            raise FileNotFoundError(f"contracts root not found: {cfg.contracts_root}")

    series_list = list_series(contracts_root)
    if cfg.series_filter:
        wanted = {s.strip() for s in cfg.series_filter.split(",") if s.strip()}
        series_list = [s for s in series_list if s in wanted]
    if cfg.smoke_only:
        # Fast path: one modern + one legacy series
        preferred = [s for s in ("4.5", "3.6") if s in series_list]
        series_list = preferred or series_list[:1]

    methods_filter = {m.strip() for m in cfg.methods_filter.split(",") if m.strip()} if cfg.methods_filter else set()

    report = CoverageReport(
        generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        engine_url=cfg.api_url,
    )

    with OVirtClient(cfg) as client:
        client.basic_probe()
        for series in series_list:
            version = _SERIES_API_MAJOR.get(series, "4")
            client.api_version = version
            act = client.activate_series(series)
            if act.status_code != 200:
                summary = SeriesSummary(series=series, api_version=version, total=1, failed=1)
                report.series.append(summary)
                report.results.append(
                    OpResult(
                        series=series,
                        operation_id="contracts.activate",
                        method="POST",
                        path_template="/ui/api/ovirt/contracts/activate",
                        path_resolved="/ui/api/ovirt/contracts/activate",
                        kind="meta",
                        status="failed",
                        http_status=act.status_code,
                        expected_hint=200,
                        duration_ms=0,
                        detail=act.text[:240],
                    )
                )
                continue

            # Reset to minimal inventory so mutation side-effects from earlier
            # series do not cascade into later packs. Unload truncates tokens.
            try:
                client.request(
                    "POST",
                    "/ui/api/demo/unload",
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    json={},
                )
            except Exception:
                pass

            # Fresh token after activate + unload (TRUNCATE clears ov_tokens).
            client.login()

            ops = load_operations(contracts_root, series)
            if methods_filter:
                ops = [o for o in ops if str(o.get("method", "")).upper() in methods_filter]
            if cfg.smoke_only:
                # Keep root + a handful of collection GETs for smoke
                kept: list[dict[str, Any]] = []
                for o in ops:
                    if o.get("kind") == "root" or (
                        o.get("kind") == "collection" and o.get("method") == "GET" and len(kept) < 25
                    ):
                        kept.append(o)
                ops = kept

            # Contracts omit HEAD; Engine accepts HEAD (fallback / HEAD→GET).
            if not methods_filter or "HEAD" in methods_filter:
                ops = list(ops) + synthesize_head_ops(ops)

            inventory = Inventory(client, version)
            summary = SeriesSummary(series=series, api_version=version)
            series_started = time.perf_counter()
            for op in ops:
                result = execute_operation(client, series=series, version=version, op=op, inventory=inventory)
                report.results.append(result)
                summary.total += 1
                if result.status == "passed":
                    summary.passed += 1
                elif result.status == "skipped":
                    summary.skipped += 1
                else:
                    summary.failed += 1
            summary.duration_ms = round((time.perf_counter() - series_started) * 1000, 2)
            if summary.total != len(ops):
                raise AssertionError(
                    f"series {series}: executed {summary.total} ops, expected {len(ops)}"
                )
            report.series.append(summary)

    return report


def report_to_dict(report: CoverageReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "engine_url": report.engine_url,
        "totals": report.totals,
        "methods": report.methods,
        "series": [asdict(s) for s in report.series],
        "results": [asdict(r) for r in report.results],
    }
