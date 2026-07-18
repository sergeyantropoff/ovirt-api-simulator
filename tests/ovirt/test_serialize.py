"""XML/JSON representation helpers."""

from __future__ import annotations

from app.ovirt.serialize import (
    collection_to_json,
    collection_to_xml,
    entity_to_json,
    entity_to_xml,
    parse_body,
)


def test_entity_json_and_xml() -> None:
    data = {"id": "1", "href": "/ovirt-engine/api/vms/1", "name": "vm1", "status": "down"}
    assert entity_to_json("vm", data)["vm"]["name"] == "vm1"
    xml = entity_to_xml("vm", data)
    assert 'id="1"' in xml
    assert "<name>vm1</name>" in xml


def test_collection_json() -> None:
    items = [{"id": "1", "name": "a"}, {"id": "2", "name": "b"}]
    body = collection_to_json("vm", items)
    assert len(body["vm"]) == 2
    xml = collection_to_xml("vms", "vm", items)
    assert "<vms>" in xml
    assert xml.count("<vm") >= 2


def test_parse_json_and_xml() -> None:
    assert parse_body(b'{"vm":{"name":"x"}}', "application/json")["vm"]["name"] == "x"
    xml = b'<vm><name>y</name></vm>'
    parsed = parse_body(xml, "application/xml")
    assert "vm" in parsed
