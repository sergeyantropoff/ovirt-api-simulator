**Language / Язык:** [English](README.md) | [Русский](README.ru.md)

# ovirt-api-simulator

Stateful laboratory simulator for the **oVirt / RHV Engine REST API**. Use it to
test API clients and infrastructure tooling without a real Engine or hypervisors.

> **Lab only.** This is not a production Engine, does not run hypervisors, and
> ships with default credentials plus a self-signed TLS certificate. Do not
> expose it to untrusted networks.

The simulator is backed by PostgreSQL, driven by generated Engine contract packs,
and exposes the same `/ovirt-engine/api` and SSO OAuth2 surfaces as oVirt Engine.
Semantic handlers persist mutations; long-running work is tracked as Engine jobs.

## Quick start (development checkout)

```bash
cp .env.example .env
make up
make seed          # or: make seed-small|seed-large|seed-big
```

| Surface | URL |
|---------|-----|
| Web UI console | http://127.0.0.1:5000 |
| Engine API | https://127.0.0.1/ovirt-engine/api |

Only **two** host ports are published by default: Engine `443` and UI `5000`.
Override with `OVIRT_ENGINE_PORT` / `OVIRT_UI_PORT` if those are taken.

**Credentials:** `admin@internal` / `secret`  
Also: `ops@internal`, `developer@internal`, `demo@internal` / `secret`

```bash
# OAuth password grant
curl -k -X POST https://127.0.0.1/ovirt-engine/sso/oauth/token \
  -d 'grant_type=password&username=admin@internal&password=secret&scope=ovirt-app-api'

# List VMs (HTTP Basic)
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms
```

## Quick start (published image)

Image: [`inecs/ovirt-api-simulator`](https://hub.docker.com/r/inecs/ovirt-api-simulator)

Requires this repository checkout (gateway TLS certs and nginx config are bind-mounted):

```bash
docker compose -f docker-compose.release.yml up -d
docker compose -f docker-compose.release.yml run --rm --entrypoint python \
  simulator -m app.ovirt.seed_cli --profile minimal

curl -skf https://127.0.0.1/health/ready
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms
```

Or: `make release-up && make release-seed PROFILE=minimal`

| Surface | URL |
|---------|-----|
| Web UI console | http://127.0.0.1:5000 |
| Engine API | https://127.0.0.1/ovirt-engine/api |

**Credentials:** `admin@internal` / `secret`

## Features

- Real Engine paths: `/ovirt-engine/api`, `/ovirt-engine/api/v3|v4`, SSO OAuth2
- XML + JSON representations (`Accept` / `Content-Type`)
- Series packs **3.0–3.6, 4.3–4.5, master** with operation deltas
- Stateful PostgreSQL inventory + async jobs
- Seed profiles: `minimal`, `small` (3h/50vm), `large` (10h/1000vm), `big` (30h/2000vm)
- Web UI with oVirt branding (`#0076B6` / charcoal `#1D2226`)
- Docker Compose + Helm
- API tests + [`pulumi-tests/`](pulumi-tests/README.md) (Pulumi contract coverage)

## Make targets

```bash
make up
make up-local            # local ports via gitignored docker-compose.override.yml
make down-local          # stop stack + remove local override
make seed
make seed-large
make test-unit
make test-integration
make test-pulumi-smoke   # Pulumi smoke
make test-pulumi         # all series × all contract ops + HTML report
make pulumi-tests        # alias for test-pulumi
make test-all            # alias for test-pulumi
make push                # git add . → multi-line commit (Ctrl-D) → origin + antropoff
# make push MSG="one line"       # skip the interactive editor
```

Docker Hub release (requires `docker login` as the Hub owner; see
[Operations](docs/operations.md)):

```bash
make release                          # inecs/ovirt-api-simulator:<pyproject version> + :latest
make release VERSION=0.2.0            # override tag
make release-build                    # build/tag only, no push
make release-up && make release-seed  # run the published stack locally
```

## Documentation

| Guide | Description |
|---|---|
| [Getting started](docs/getting-started.md) | First lab session |
| [Ports](docs/ports.md) | Published Engine + UI ports |
| [Authentication](docs/authentication.md) | Basic, OAuth2, sessions |
| [API versions](docs/api-versions.md) | Series packs and Version header |
| [Configuration](docs/configuration.md) | Environment and Compose |
| [Seed profiles](docs/seed-profiles.md) | `minimal` / `small` / `large` / `big` |
| [Kubernetes / Helm](docs/kubernetes.md) | Cluster install |
| [Full index](docs/README.md) | All guides |

Russian mirrors: [`README.ru.md`](README.ru.md) and [`docs/ru/`](docs/ru/README.md).
Switch language with the header on each page.
