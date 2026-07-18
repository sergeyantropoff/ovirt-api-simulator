**Language / Язык:** [English](networks.md) | [Русский](../ru/domains/networks.md)

# Networks

| Collection | Path |
|---|---|
| Networks | `/ovirt-engine/api/networks` |
| VNIC profiles | `/ovirt-engine/api/vnicprofiles` |

VMs attach NICs that reference vNIC profiles and logical networks.

```bash
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/networks
```

Related: [Virtual machines](vms.md).
