**Language / Язык:** [English](../../domains/hosts.md) | [Русский](hosts.md)

# Hosts

| Коллекция | Путь |
|---|---|
| Hosts | `/ovirt-engine/api/hosts` |

Хосты принадлежат cluster и участвуют в размещении ВМ в лабораторных сценариях.

```bash
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/hosts
```

Demo seed создаёт несколько хостов для ~1000 ВМ. Связанное:
[Datacenters и clusters](datacenters-clusters.md).
