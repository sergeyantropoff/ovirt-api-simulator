**Language / Язык:** [English](operations.md) | [Русский](ru/operations.md)

# Operations

## Day-2 Compose

```bash
make up            # build + start + wait
make restart       # force recreate
make logs          # follow all services
make down          # stop
make seed          # reload minimal
make seed-demo     # reload demo (~1000 VMs)
make smoke         # Basic auth + list VMs
```

## Migrations

The `migrate` Compose service / Helm init container runs
`python -m app.db.migrate_cli` before the simulator becomes ready. Do not point
clients at Engine until `/health/ready` succeeds.

Schema history starts at `001_ovirt_core.sql`. If you upgraded from an earlier
pre-release lab DB, recreate the volume:

```bash
docker compose down -v
make up && make seed
```

## Reseed

Reseed **truncates** laboratory tables. Prefer `minimal` in shared CI jobs;
use `demo` when you need density.

```bash
make seed-demo
# or Web UI → Data → demo
```

## Series change

**Cold start** — change `OVIRT_SERIES` and recreate the simulator container:

```bash
OVIRT_SERIES=4.4 make restart
```

**Hot-swap** (in-memory, no rebuild) — Web UI **API catalog** → **Apply as runtime**, or:

```bash
curl -s http://127.0.0.1:5000/ui/api/ovirt/contracts/activate \
  -H 'Content-Type: application/json' \
  -d '{"series":"4.4"}'
```

See [API versions](api-versions.md) and [Web UI](web-ui.md).

## Client lab cleanup

```bash
make clean-test-resources
```

Removes resources created by [`pulumi-tests/`](../pulumi-tests/README.md).

## Publish to Docker Hub

`make release` builds the **runtime** image (production target — not the local
bind-mounted `dev` image) and pushes it to Docker Hub:

```bash
docker login   # once; account must own or can push to DOCKERHUB_USER
make release
```

Defaults:

| Variable | Default | Meaning |
|---|---|---|
| `DOCKERHUB_USER` | `inecs` | Docker Hub namespace/org |
| `IMAGE_NAME` | `ovirt-api-simulator` | Repository name |
| `VERSION` | from `pyproject.toml` | Image tag |
| `PUSH_LATEST` | `1` | Also tag/push `:latest` |

Examples:

```bash
make release
make release VERSION=0.2.0
make release DOCKERHUB_USER=myorg PUSH_LATEST=0
make release-build   # build/tag locally without pushing
```

Published tags:

- `inecs/ovirt-api-simulator:<version>`
- `inecs/ovirt-api-simulator:latest` (unless `PUSH_LATEST=0`)

## Quick start with the published compose file

[`docker-compose.release.yml`](../docker-compose.release.yml) pulls the Hub
runtime image and starts PostgreSQL + migrate + simulator + Engine gateway:

```bash
docker compose -f docker-compose.release.yml up -d
docker compose -f docker-compose.release.yml run --rm --entrypoint python \
  simulator -m app.ovirt.seed_cli --profile minimal

curl -skf https://127.0.0.1/health/ready
```

Helpers from a git checkout:

```bash
make release-up
make release-seed PROFILE=minimal
# or: make release-seed PROFILE=demo
make release-down
```
