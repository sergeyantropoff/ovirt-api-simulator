"""Resolve oVirt Engine series contract pack locations."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.ovirt.opspec import OperationSpec, SeriesPack

_SERIES_MAJOR = {
    "3.0": 30,
    "3.1": 31,
    "3.2": 32,
    "3.3": 33,
    "3.4": 34,
    "3.5": 35,
    "3.6": 36,
    "4.3": 43,
    "4.4": 44,
    "4.5": 45,
    "master": 50,
}
_MAJOR_SERIES = {v: k for k, v in _SERIES_MAJOR.items()}


def contracts_root() -> Path:
    """Locate ``contracts/ovirt`` for source, wheel, or Docker layouts."""

    env = os.environ.get("OVIRT_CONTRACTS_ROOT")
    if env:
        return Path(env)

    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "contracts" / "ovirt",  # repo checkout or site-packages
        Path("/app/contracts/ovirt"),  # runtime image WORKDIR layout
        Path.cwd() / "contracts" / "ovirt",
    ]
    for path in candidates:
        if path.is_dir():
            return path
    return candidates[0]


def series_for_major(major: int) -> str:
    return _MAJOR_SERIES.get(major, "4.5")


def major_for_series(series: str) -> int:
    return _SERIES_MAJOR.get(series.lower(), 45)


def list_series() -> list[dict[str, Any]]:
    root = contracts_root()
    if not root.exists():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(root.iterdir()):
        man = path / "manifest.json"
        if not man.is_file():
            continue
        data = json.loads(man.read_text())
        result.append(
            {
                "series": data.get("series", path.name),
                "major": data.get("major", major_for_series(path.name)),
                "api_version": data.get("api_version", "4"),
                "operation_count": data.get("operation_count", 0),
                "service_count": data.get("service_count", 1),
                "checksum": data.get("checksum", ""),
                "generated_at": data.get("generated_at", ""),
                "deltas": data.get("deltas", {}),
                "product": data.get("product", {}),
            }
        )
    return result


def _op_from_dict(raw: dict[str, Any]) -> OperationSpec:
    return OperationSpec(
        operation_id=str(raw["operation_id"]),
        method=raw["method"],
        path=str(raw["path"]),
        resource_type=str(raw.get("resource_type") or "object"),
        collection_key=str(raw.get("collection_key") or "objects"),
        element=str(raw.get("element") or raw.get("resource_type") or "object"),
        kind=str(raw.get("kind") or "collection"),
        search=bool(raw.get("search", False)),
        introduced_in=str(raw.get("introduced_in") or "3.0"),
        requires_auth=bool(raw.get("requires_auth", True)),
        status_code=int(raw.get("status_code") or 200),
        create_status=int(raw.get("create_status") or 201),
        notes=str(raw.get("notes") or ""),
        response_fixture=raw.get("response_fixture"),
    )


def load_series_pack(series: str) -> SeriesPack:
    series = series.lower()
    series_dir = contracts_root() / series
    man_path = series_dir / "manifest.json"
    api_path = series_dir / "api.json"
    if not man_path.is_file() or not api_path.is_file():
        raise FileNotFoundError(f"oVirt contract pack not found: {series_dir}")
    man = json.loads(man_path.read_text())
    data = json.loads(api_path.read_text())
    ops = [_op_from_dict(raw) for raw in data.get("operations") or []]
    return SeriesPack(
        series=str(man.get("series", series)),
        api_version=str(man.get("api_version") or data.get("api_version") or "4"),
        major=int(man.get("major") or major_for_series(series)),
        operations=ops,
        product=dict(man.get("product") or data.get("product") or {}),
        entry_point_links=list(man.get("entry_point_links") or []),
        checksum=str(man.get("checksum") or ""),
    )


@dataclass
class ContractRuntime:
    series: str = "4.5"
    pack: SeriesPack | None = None
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def reload(self, series: str | None = None) -> dict[str, Any]:
        with self._lock:
            target = (series or self.series).lower()
            self.pack = load_series_pack(target)
            self.series = target
            return self.summary()

    def summary(self) -> dict[str, Any]:
        with self._lock:
            pack = self.pack
            if pack is None:
                return {
                    "series": self.series,
                    "operation_count": 0,
                    "major": major_for_series(self.series),
                }
            return {
                "series": pack.series,
                "major": pack.major,
                "api_version": pack.api_version,
                "operation_count": pack.operation_count(),
                "service_count": 1,
                "checksum": pack.checksum,
                "product": pack.product,
                "deltas": next(
                    (s.get("deltas") for s in list_series() if s["series"] == pack.series),
                    {},
                ),
            }


_RUNTIME = ContractRuntime()


def get_runtime() -> ContractRuntime:
    return _RUNTIME


def ensure_loaded(series: str = "4.5") -> ContractRuntime:
    rt = get_runtime()
    if rt.pack is None:
        try:
            rt.reload(series)
        except FileNotFoundError:
            pass
    return rt
