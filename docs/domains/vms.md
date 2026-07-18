**Language / Язык:** [English](vms.md) | [Русский](../ru/domains/vms.md)

# Virtual machines

| Collection | Path |
|---|---|
| VMs | `/ovirt-engine/api/vms` |
| Templates | `/ovirt-engine/api/templates` |

Nested resources (disk attachments, NICs, snapshots) are available under each VM
id where the pack declares them.

```bash
# List
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms

# Create (JSON sketch)
curl -k -u 'admin@internal:secret' -H 'Content-Type: application/json' -H 'Version: 4' \
  -d '{"name":"lab-vm-1","cluster":{"name":"Default"}}' \
  https://127.0.0.1/ovirt-engine/api/vms
```

Long-running actions surface as Engine [jobs](jobs.md). Client suites exercise
create/get/modify/delete VM plus disk and NIC flows — see
[`pulumi-tests/`](../../pulumi-tests/README.md).
