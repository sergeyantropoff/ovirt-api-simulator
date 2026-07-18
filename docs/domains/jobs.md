**Language / Язык:** [English](jobs.md) | [Русский](../ru/domains/jobs.md)

# Jobs & events

| Collection | Path |
|---|---|
| Jobs | `/ovirt-engine/api/jobs` |
| Events | `/ovirt-engine/api/events` |

Long-running Engine operations create job records with steps. Seed inserts a
finished sample job. Events capture inventory lifecycle signals for lab
inspection.

```bash
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/jobs
```

Task timing can be accelerated with `SIMULATION_TIME_SCALE`
([configuration.md](../configuration.md)).
