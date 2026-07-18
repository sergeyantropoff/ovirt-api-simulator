"""Console body examples use minimal-seed IDs and Engine-shaped roots."""

from __future__ import annotations

from app.ovirt.ids import stable_id
from app.web.ovirt_body_examples import body_example_for
from app.web.ovirt_catalog import path_param_example


def test_path_params_use_minimal_seed_ids() -> None:
    assert path_param_example("vmId") == str(stable_id("vm", "lab-vm-01"))
    assert path_param_example("hostId") == str(stable_id("host", "host01"))
    assert path_param_example("clusterId") == str(stable_id("cluster", "Default"))
    assert path_param_example("storageDomainId") == str(stable_id("sd", "data1"))


def test_post_vm_body_is_root_wrapped_with_cluster_ref() -> None:
    body = body_example_for(method="POST", kind="collection", element="vm", path="/vms")
    assert body is not None
    assert "vm" in body
    vm = body["vm"]
    assert vm["cluster"]["id"] == str(stable_id("cluster", "Default"))
    assert vm["template"]["name"] == "Blank"


def test_disk_attachment_creates_disk_inline() -> None:
    body = body_example_for(
        method="POST",
        kind="collection",
        element="disk_attachment",
        path="/vms/{vm_id}/diskattachments",
    )
    assert body is not None
    disk = body["disk_attachment"]["disk"]
    assert "id" not in disk
    assert disk["name"] == "example-attached-disk"
    assert disk["provisioned_size"] == 10737418240


def test_put_does_not_rename_entity() -> None:
    body = body_example_for(method="PUT", kind="item", element="vm", path="/vms/{vm_id}")
    assert body is not None
    assert "name" not in body["vm"]
    assert body["vm"]["description"].startswith("Updated")


def test_action_start_uses_action_root() -> None:
    body = body_example_for(
        method="POST", kind="action", element="action", path="/vms/{vm_id}/start"
    )
    assert body == {"action": {"async": True}}


def test_body_fields_derived_from_example_for_params_drawer() -> None:
    from app.web.ovirt_catalog import _body_fields_from_example, ovirt_method_payload

    fields = _body_fields_from_example(
        {"bookmark": {"name": "example-bookmark", "value": "Vms: status=up"}},
        element="bookmark",
    )
    names = {f["name"] for f in fields}
    assert names == {"name", "value"}

    payload = ovirt_method_payload(
        major=45,
        path="/ovirt-engine/api/bookmarks",
        verb="POST",
        runtime_version="ovirt-4.5",
    )
    assert payload["body_example"] is not None
    assert "bookmark" in payload["body_example"]
    field_names = {f["name"] for f in payload["body_fields"]}
    assert "name" in field_names
    assert "value" in field_names


def test_body_fields_include_nested_vm_example_paths() -> None:
    from app.web.ovirt_catalog import _body_fields_from_example, ovirt_method_payload
    from app.web.ovirt_body_examples import body_example_for

    example = body_example_for(
        method="POST",
        kind="collection",
        element="vm",
        path="/ovirt-engine/api/vms",
    )
    fields = _body_fields_from_example(example, element="vm")
    names = {f["name"] for f in fields}
    assert "name" in names
    assert "memory" in names
    assert "cpu.topology.sockets" in names
    assert "os.type" in names
    assert "cluster.id" in names
    assert "template.name" in names

    payload = ovirt_method_payload(
        major=45,
        path="/ovirt-engine/api/vms",
        verb="POST",
        runtime_version="ovirt-4.5",
    )
    nested = {f["name"] for f in payload["body_fields"]}
    assert "cluster.id" in nested
    assert "cpu.topology.cores" in nested
