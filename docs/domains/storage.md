**Language / Язык:** [English](storage.md) | [Русский](../ru/domains/storage.md)

# Storage

| Collection | Path |
|---|---|
| Storage domains | `/ovirt-engine/api/storagedomains` |
| Storage connections | `/ovirt-engine/api/storageconnections` |
| Disks | `/ovirt-engine/api/disks` |

Seed attaches storage domains to the datacenter and creates sample disks for
VMs. Disk attach/expand/delete paths are covered by client P0 smokes.

```bash
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/storagedomains

curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/disks
```
