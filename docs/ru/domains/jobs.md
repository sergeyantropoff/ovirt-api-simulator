**Language / Язык:** [English](../../domains/jobs.md) | [Русский](jobs.md)

# Jobs и events

| Коллекция | Путь |
|---|---|
| Jobs | `/ovirt-engine/api/jobs` |
| Events | `/ovirt-engine/api/events` |

Длительные операции Engine создают записи jobs со steps. Seed вставляет
завершённый sample job. Events фиксируют сигналы жизненного цикла инвентаря для
лабораторного просмотра.

```bash
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/jobs
```

Длительность задач можно ускорить через `SIMULATION_TIME_SCALE`
([configuration.md](../configuration.md)).
