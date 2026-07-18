**Language / Язык:** [English](hosts.md) | [Русский](../ru/domains/hosts.md)

# Hosts

| Collection | Path |
|---|---|
| Hosts | `/ovirt-engine/api/hosts` |

Hosts belong to a cluster and participate in VM placement for lab scenarios.

```bash
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/hosts
```

Demo seed creates multiple hosts to support ~1000 VMs. Related:
[Datacenters & clusters](datacenters-clusters.md).
