**Language / Язык:** [English](seed-profiles.md) | [Русский](ru/seed-profiles.md)

# Seed profiles

| Profile | How to load | Contents |
|---|---|---|
| `minimal` | Simulator startup (if DB is not already `demo`) / `make seed` / `python -m app.ovirt.seed_cli --profile minimal` / Helm seed Job | 1 datacenter, 1 cluster, 1 host, Blank template, 4 users, small inventory sample |
| `demo` | `make seed-demo` / UI Data drawer / Helm `seed.profile=demo` / `--profile demo` | ~1000 VMs, multi-host DC, networks, storage domains, disks, nested samples |

On Compose, the FastAPI lifespan loads **`minimal`** automatically when the DB
is empty or not marked as `demo`. Use `make seed-demo` (or the UI Data drawer)
for the large profile. Helm can also run a seed Job (`seed.enabled`).

Password for all users: **`secret`**. Domain: **`internal`**.

Principals: `admin@internal`, `ops@internal`, `developer@internal`,
`demo@internal`.

## CLI

```bash
make seed
make seed-demo

# equivalent
docker compose run --rm --entrypoint python simulator \
  -m app.ovirt.seed_cli --profile demo
```

## Helm

```yaml
seed:
  enabled: true
  profile: demo   # or minimal
```

## Behaviour

Both profiles **truncate** oVirt lab tables then reload. Prefer `demo` for
density and nested GET probes; `minimal` for fast CI.
