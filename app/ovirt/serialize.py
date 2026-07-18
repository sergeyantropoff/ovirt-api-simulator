"""XML and JSON representation helpers for oVirt Engine API."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import Request
from fastapi.responses import JSONResponse, Response

_XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'


def wants_xml(request: Request) -> bool:
    accept = (request.headers.get("accept") or "").lower()
    if "application/json" in accept or "+json" in accept:
        return False
    if "application/xml" in accept or "text/xml" in accept or "+xml" in accept:
        return True
    # Engine historically defaults to XML
    return True


def parse_body(raw: bytes, content_type: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    ct = (content_type or "").lower()
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return {}
    if "json" in ct or text.startswith("{") or text.startswith("["):
        data = json.loads(text)
        return data if isinstance(data, dict) else {"value": data}
    # Minimal XML → dict (element children)
    try:
        from xml.etree.ElementTree import fromstring

        root = fromstring(text)
        return {root.tag: _xml_node(root)}
    except Exception:
        return {"raw": text}


def _xml_node(el: Element) -> Any:
    children = list(el)
    data: dict[str, Any] = {}
    if el.attrib:
        data.update({f"@{k}": v for k, v in el.attrib.items()})
    if not children:
        text = (el.text or "").strip()
        if data:
            if text:
                data["#text"] = text
            return data
        return text
    for child in children:
        value = _xml_node(child)
        if child.tag in data:
            existing = data[child.tag]
            if not isinstance(existing, list):
                data[child.tag] = [existing]
            data[child.tag].append(value)
        else:
            data[child.tag] = value
    return data


def unwrap_entity(payload: dict[str, Any], element: str) -> dict[str, Any]:
    if element in payload and isinstance(payload[element], dict):
        return dict(payload[element])
    # XML parse nests under root tag
    if len(payload) == 1:
        only = next(iter(payload.values()))
        if isinstance(only, dict):
            return dict(only)
    return dict(payload)


def _to_xml_value(parent: Element, key: str, value: Any) -> None:
    if value is None:
        return
    if isinstance(value, dict):
        attrs = {k[1:]: str(v) for k, v in value.items() if k.startswith("@")}
        body = {k: v for k, v in value.items() if not k.startswith("@")}
        node = SubElement(parent, key, attrs)
        if "#text" in body and len(body) == 1:
            node.text = str(body["#text"])
            return
        for ck, cv in body.items():
            if ck == "#text":
                node.text = str(cv)
            else:
                _to_xml_value(node, ck, cv)
        return
    if isinstance(value, list):
        for item in value:
            _to_xml_value(parent, key, item)
        return
    if isinstance(value, bool):
        SubElement(parent, key).text = "true" if value else "false"
        return
    if isinstance(value, datetime):
        SubElement(parent, key).text = value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return
    SubElement(parent, key).text = str(value)


def entity_to_xml(element: str, data: dict[str, Any]) -> str:
    attrs = {}
    if "id" in data:
        attrs["id"] = str(data["id"])
    if "href" in data:
        attrs["href"] = str(data["href"])
    root = Element(element, attrs)
    for key, value in data.items():
        if key in {"id", "href"}:
            continue
        _to_xml_value(root, key, value)
    return _XML_DECL + tostring(root, encoding="unicode")


def collection_to_xml(collection: str, element: str, items: list[dict[str, Any]]) -> str:
    root = Element(collection)
    for item in items:
        child_xml = entity_to_xml(element, item)
        # strip decl and wrap
        from xml.etree.ElementTree import fromstring

        root.append(fromstring(re.sub(r"^<\?xml[^?]*\?>", "", child_xml)))
    return _XML_DECL + tostring(root, encoding="unicode")


def entity_to_json(element: str, data: dict[str, Any]) -> dict[str, Any]:
    return {element: data}


def collection_to_json(element: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    # Engine JSON uses singular key with array
    return {element: items}


def respond(
    request: Request,
    *,
    element: str,
    data: dict[str, Any] | list[dict[str, Any]] | None = None,
    collection: str | None = None,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> Response:
    as_xml = wants_xml(request)
    hdrs = dict(headers or {})
    if collection is not None and isinstance(data, list):
        if as_xml:
            body = collection_to_xml(collection, element, data)
            return Response(content=body, status_code=status_code, media_type="application/xml", headers=hdrs)
        return JSONResponse(
            content=collection_to_json(element, data),
            status_code=status_code,
            headers=hdrs,
        )
    payload = data if isinstance(data, dict) else {}
    if as_xml:
        return Response(
            content=entity_to_xml(element, payload),
            status_code=status_code,
            media_type="application/xml",
            headers=hdrs,
        )
    return JSONResponse(content=entity_to_json(element, payload), status_code=status_code, headers=hdrs)
