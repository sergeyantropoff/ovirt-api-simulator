**Language / Язык:** [English](seed-profiles.md) | [Русский](ru/seed-profiles.md)

# Seed profiles

| Profile | How to load | Contents |
|---|---|---|
| `minimal` | Startup (if DB is not a sized demo) / `make seed` / `--profile minimal` | 1 DC, 1 cluster, 1 host, Blank template, 4 users |
| `small` | `make seed-small` / DATA → **Load small** / `--profile small` | **3 hosts · 50 VMs** · 1 DC · 1 cluster · 2 networks · 2 SD |
| `large` | `make seed-large` / DATA → **Load large** / `--profile large` | **10 hosts · 1000 VMs** · 2 DC · 2 clusters · proportional inventory |
| `big` | `make seed-big` / DATA → **Load big** / `--profile big` | **30 hosts · 2000 VMs** · 3 DC · 6 clusters · denser tags/events/jobs |
| `demo` | `make seed-demo` (alias) / `--profile demo` | Same as **`large`** (legacy name) |

Sized demos scale datacenters, clusters, hosts, VMs, networks, storage domains,
templates, tags, events, jobs, and nested samples together. On Compose, lifespan
keeps any of `small` / `large` / `big` / `demo` across restarts (does not wipe to
minimal).

Password for all users: **`secret`**. Domain: **`internal`**.

Principals: `admin@internal`, `ops@internal`, `developer@internal`,
`demo@internal`.

## CLI

```bash
make seed
make seed-small
make seed-large   # or: make seed-demo
make seed-big

docker compose run --rm --entrypoint python simulator \
  -m app.ovirt.seed_cli --profile large
```

## UI

Open the **DATA** drawer → **Load small** / **Load large** / **Load big**, or
**Reset to minimal**.

API: `POST /ui/api/demo/load?size=small|large|big`

## Helm

```yaml
seed:
  enabled: true
  profile: large   # minimal | small | large | big | demo
```

## Behaviour

All profiles **truncate** oVirt lab tables then reload. Prefer `large`/`big` for
density; `minimal` / `small` for fast CI and light labs.
