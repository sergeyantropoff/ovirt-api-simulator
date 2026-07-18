**Language / Язык:** [English](../../domains/datacenters-clusters.md) | [Русский](datacenters-clusters.md)

# Datacenters и clusters

| Коллекция | Путь |
|---|---|
| Datacenters | `/ovirt-engine/api/datacenters` |
| Clusters | `/ovirt-engine/api/clusters` |

Minimal seed создаёт один datacenter и один cluster. Demo seed увеличивает число
хостов и плотность ВМ в той же топологии.

```bash
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/datacenters

curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/clusters
```

Связанное: [Hosts](hosts.md), [Виртуальные машины](vms.md).
