**Language / Язык:** [English](../../domains/networks.md) | [Русский](networks.md)

# Сети

| Коллекция | Путь |
|---|---|
| Networks | `/ovirt-engine/api/networks` |
| VNIC profiles | `/ovirt-engine/api/vnicprofiles` |

ВМ подключают NIC, ссылающиеся на vNIC profiles и логические сети.

```bash
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/networks
```

Связанное: [Виртуальные машины](vms.md).
