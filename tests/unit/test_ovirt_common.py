"""Unit tests for native Engine NotFound helpers."""

from __future__ import annotations

import pytest

from app.ovirt.common import no_such
from app.ovirt.errors import OVirtError, fault_body
from app.ovirt.repr import generic_entity


def test_no_such_includes_id_in_detail() -> None:
    err = no_such("host", "pve01-bad-id")
    assert isinstance(err, OVirtError)
    assert err.status_code == 404
    assert err.reason == "NotFound"
    assert err.detail == "No such host ('pve01-bad-id')"


def test_no_such_fault_body_is_json_not_html() -> None:
    err = no_such("datacenter", "missing-dc")
    body = fault_body(err, as_xml=False)
    assert body == {
        "fault": {"reason": "NotFound", "detail": "No such datacenter ('missing-dc')"}
    }
    xml = fault_body(err, as_xml=True)
    assert isinstance(xml, str)
    assert "No such datacenter ('missing-dc')" in xml
    assert "<html" not in xml.lower()


def test_generic_entity_none_raises_no_such() -> None:
    with pytest.raises(OVirtError, match=r"No such host \('abc'\)") as caught:
        generic_entity("hosts", "host", None, entity_id="abc")
    assert caught.value.status_code == 404
