**Language / Язык:** [English](../../domains/storage.md) | [Русский](storage.md)

# Storage

| Коллекция | Путь |
|---|---|
| Storage domains | `/ovirt-engine/api/storagedomains` |
| Storage connections | `/ovirt-engine/api/storageconnections` |
| Disks | `/ovirt-engine/api/disks` |

Seed подключает storage domains к datacenter и создаёт sample-диски для ВМ.
Пути attach/expand/delete дисков покрыты клиентскими P0 smoke.

```bash
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/storagedomains

curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/disks
```
