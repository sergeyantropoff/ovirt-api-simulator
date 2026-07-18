**Language / Язык:** [English](datacenters-clusters.md) | [Русский](../ru/domains/datacenters-clusters.md)

# Datacenters & clusters

| Collection | Path |
|---|---|
| Datacenters | `/ovirt-engine/api/datacenters` |
| Clusters | `/ovirt-engine/api/clusters` |

Minimal seed creates one datacenter and one cluster. Demo seed expands hosts and
VM density under the same topology.

```bash
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/datacenters

curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/clusters
```

Related: [Hosts](hosts.md), [Virtual machines](vms.md).
