"""Contract operation specifications for Engine API packs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]


@dataclass(frozen=True)
class OperationSpec:
    operation_id: str
    method: HttpMethod
    path: str
    resource_type: str
    collection_key: str
    element: str
    kind: str = "collection"
    search: bool = False
    introduced_in: str = "3.0"
    requires_auth: bool = True
    status_code: int = 200
    create_status: int = 201
    notes: str = ""
    response_fixture: Any | None = None


@dataclass
class SeriesPack:
    series: str
    api_version: str
    major: int
    operations: list[OperationSpec] = field(default_factory=list)
    product: dict[str, str] = field(default_factory=dict)
    entry_point_links: list[dict[str, str]] = field(default_factory=list)
    checksum: str = ""

    def operation_count(self) -> int:
        return len(self.operations)
