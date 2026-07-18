from app.ovirt.versioning import strip_api_prefix


def test_strip_prefix():
    assert strip_api_prefix("/ovirt-engine/api/vms") == "/vms"
    assert strip_api_prefix("/ovirt-engine/api/v4/vms") == "/vms"
    assert strip_api_prefix("/ovirt-engine/api/v3/hosts") == "/hosts"
