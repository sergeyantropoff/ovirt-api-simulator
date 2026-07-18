**Language / Язык:** [English](getting-started.md) | [Русский](ru/getting-started.md)

# Getting started

Bring up a local Engine lab, authenticate, and run a first read against the
simulator.

## Prerequisites

- Docker and Docker Compose
- `make` (optional but used by the documented commands)

Python, linters, and tests run **inside** containers. You do not need a local
Python toolchain for day-to-day use.

## Choose a path

| Path | When to use |
|---|---|
| [Development checkout](#1a-development-checkout) | Contribute / bind-mount source |
| [Published image](#1b-published-image) | Fastest lab using the Hub image |
| [Helm / Kubernetes](kubernetes.md) | Cluster install (no nginx gateway yet) |

## 1a. Development checkout

```bash
cp .env.example .env
make install
make up
make seed
```

| Host port | Service |
|---|---|
| `443` | Engine API + SSO (HTTPS) |
| `5000` | Web UI console (HTTP) |

Only these two ports are published. Internal FastAPI listens on `:8080` inside
the compose network. See [Ports](ports.md).

Migrations run automatically via the `migrate` one-shot service.

## 1b. Published image

Uses [`docker-compose.release.yml`](../docker-compose.release.yml) — PostgreSQL +
migrate + simulator + Engine gateway from the Hub runtime image:

```bash
docker compose -f docker-compose.release.yml pull
docker compose -f docker-compose.release.yml up -d
docker compose -f docker-compose.release.yml run --rm --entrypoint python \
  simulator -m app.ovirt.seed_cli --profile minimal
```

Override the tag with `IMAGE_TAG=0.1.0` if needed. From a git checkout:

```bash
make release-up
make release-seed PROFILE=minimal
```

## 2. Wait until ready

```bash
curl -skf https://127.0.0.1/health/ready
curl -sf http://127.0.0.1:5000/health/live
```

`/health/ready` returns HTTP 503 until PostgreSQL is reachable **and** the
latest packaged migration is applied.

## 3. Seed a profile

```bash
make seed          # minimal lab
# or
make seed-demo     # ~1000 VMs
```

See [Seed profiles](seed-profiles.md).

## 4. Authenticate and list VMs

```bash
curl -k -u 'admin@internal:secret' \
  -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms
```

Or obtain an OAuth token:

```bash
curl -k -X POST https://127.0.0.1/ovirt-engine/sso/oauth/token \
  -d 'grant_type=password&username=admin@internal&password=secret&scope=ovirt-app-api'
```

Details: [Authentication](authentication.md).

## 5. Open the Web UI

Browse [http://127.0.0.1:5000/](http://127.0.0.1:5000/) — Auth drawer, API
catalog, coverage, and Data reseed controls. See [Web UI](web-ui.md).

## Next steps

- [API versions](api-versions.md) — switch series packs (`OVIRT_SERIES`)
- [Clients & examples](examples/overview.md) — cookbooks
- [Domains](domains/README.md) — VMs, storage, networks
- [Troubleshooting](troubleshooting.md) — common failures
