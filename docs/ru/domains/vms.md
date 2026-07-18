**Language / Язык:** [English](../../domains/vms.md) | [Русский](vms.md)

# Виртуальные машины

| Коллекция | Путь |
|---|---|
| VMs | `/ovirt-engine/api/vms` |
| Templates | `/ovirt-engine/api/templates` |

Вложенные ресурсы (disk attachments, NIC, snapshots) доступны под id ВМ, если
они объявлены в pack.

```bash
# Список
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms

# Создание (эскиз JSON)
curl -k -u 'admin@internal:secret' -H 'Content-Type: application/json' -H 'Version: 4' \
  -d '{"name":"lab-vm-1","cluster":{"name":"Default"}}' \
  https://127.0.0.1/ovirt-engine/api/vms
```

Длительные действия отражаются как Engine [jobs](jobs.md). Клиентские suites
проверяют create/get/modify/delete ВМ, а также диски и NIC — см.
[`pulumi-tests/`](../../../pulumi-tests/README.ru.md).
