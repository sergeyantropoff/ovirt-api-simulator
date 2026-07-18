"""oVirt Engine fault responses (XML/JSON)."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, Response


class OVirtError(Exception):
    def __init__(
        self,
        reason: str,
        detail: str,
        *,
        status_code: int = 400,
        code: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail
        self.status_code = status_code
        self.code = code or reason


def _wants_xml(request: Request) -> bool:
    accept = (request.headers.get("accept") or "").lower()
    content = (request.headers.get("content-type") or "").lower()
    if "application/xml" in accept or "text/xml" in accept:
        return True
    if "json" in accept:
        return False
    if "xml" in content:
        return True
    # Engine default is XML when Accept is omitted / */*
    return "json" not in accept


def fault_body(error: OVirtError, *, as_xml: bool) -> str | dict[str, Any]:
    if as_xml:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f"<fault><reason>{_esc(error.reason)}</reason>"
            f"<detail>{_esc(error.detail)}</detail></fault>"
        )
    return {"fault": {"reason": error.reason, "detail": error.detail}}


def _esc(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


async def ovirt_error_handler(request: Request, exc: OVirtError) -> Response:
    as_xml = _wants_xml(request)
    body = fault_body(exc, as_xml=as_xml)
    if as_xml:
        return Response(
            content=str(body),
            status_code=exc.status_code,
            media_type="application/xml",
        )
    return JSONResponse(content=body, status_code=exc.status_code)
