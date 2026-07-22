**Language / Язык:** [English](configuration.md) | [Русский](ru/configuration.md)

# Configuration

Application settings are loaded from the environment (see `.env.example`).
Docker Compose injects many of these for the `simulator` service.

## Core

| Variable | Default / example | Meaning |
|---|---|---|
| `APP_HOST` | `0.0.0.0` | Bind address |
| `APP_PORT` | `8080` | Internal FastAPI port (not the public Engine port) |
| `DATABASE_URL` | `postgresql://ovirt:ovirt@postgres:5432/ovirt_simulator` | asyncpg DSN |
| `TEST_DATABASE_URL` | same as above | Integration-test DSN |
| `DB_POOL_MIN_SIZE` | `1` | Pool minimum |
| `DB_POOL_MAX_SIZE` | `10` | Pool maximum |
| `LOG_LEVEL` | `INFO` | Logging level |
| `REQUEST_ID_HEADER` | `X-Request-ID` | Request correlation header |

## Engine series and seed

| Variable | Default | Meaning |
|---|---|---|
| `OVIRT_SERIES` | `4.5` | Contract pack at cold start (`3.0`–`3.6`, `4.3`–`4.5`, `master`) |
| `SEED_PROFILE` | `minimal` | Used by seed CLI / Helm seed Job (`minimal` / `demo`) |

## Security and tasks

| Variable | Meaning |
|---|---|
| `TICKET_SIGNING_KEY` | Signing material for lab tokens (**change outside toy labs**) |
| `TASK_WORKER_CONCURRENCY` | Leased asyncio workers (1–32) |
| `TASK_LEASE_SECONDS` | PostgreSQL task lease duration |
| `SIMULATION_TIME_SCALE` | Accelerates simulated job durations |

## Host publish ports

| Variable | Default | Meaning |
|---|---|---|
| `OVIRT_ENGINE_PORT` | `443` | Host → gateway `:443` (Engine HTTPS) |
| `OVIRT_UI_PORT` | `5000` | Host → gateway `:5000` (Web UI) |

See [Ports](ports.md).

## Compose

| File | Role |
|---|---|
| `docker-compose.yml` | Dev stack (build + bind mounts) |
| `docker-compose.release.yml` | Published Hub image |
| `.env` / `.env.example` | Local overrides |

Services:

- **simulator** — FastAPI on internal `8080`
- **api-gateway** — nginx publishing Engine + UI ([ports.md](ports.md))
- **postgres** — `postgres:17.5-bookworm` (host port omitted by default)
- **migrate** — one-shot schema migrations

## Helm

See [Kubernetes / Helm](kubernetes.md) and
[`helm/ovirt-api-simulator/values.yaml`](../helm/ovirt-api-simulator/values.yaml).

| Value | Purpose |
|---|---|
| `image.repository` / `image.tag` | Container image |
| `config.ovirtSeries` | Pack series env `OVIRT_SERIES` |
| `seed.profile` | `minimal` / `demo` |
| `postgresql.enabled` | Bundled DB |
| `databaseUrl` | External DSN when bundled Postgres is off |
| `secrets.ticketSigningKey` | Must be rotated for shared clusters |
| `service.port` | ClusterIP port (default `8080`) |

`gateway.*` is unused (no Compose-style nginx gateway in the chart).
`ingress.*` is optional — see
[`values-ingress-example.yaml`](../helm/ovirt-api-simulator/values-ingress-example.yaml)
and [Troubleshooting](troubleshooting.md) for annotations that preserve Engine
fault bodies.

## Contract packs

Location: `contracts/ovirt/<series>/`.

Each series has `api.json`, `manifest.json`, and `deltas.json`. Regenerate:

```bash
make generate-packs
```
