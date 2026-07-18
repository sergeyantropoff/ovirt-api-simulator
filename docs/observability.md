**Language / Язык:** [English](observability.md) | [Русский](ru/observability.md)

# Observability

## Health endpoints

| Path | Meaning |
|---|---|
| `/health/live` | Process is running |
| `/health/ready` | DB reachable + migrations applied |

Both are exposed on the simulator and via the Compose gateway (either published
port).

```bash
curl -skf https://127.0.0.1/health/ready
curl -sf http://127.0.0.1:5000/health/live
```

## Request IDs

Header `X-Request-ID` (configurable via `REQUEST_ID_HEADER`) is accepted and
echoed where middleware applies.

## Logs

Compose:

```bash
make logs
docker compose logs -f simulator api-gateway
```

Helm (chart labels use `app: ovirt-api-simulator`):

```bash
kubectl -n ovirt-sim logs -l app=ovirt-api-simulator -f
kubectl -n ovirt-sim logs -l app=ovirt-api-simulator-postgresql -f
```

## Coverage evidence

- Pack coverage: [api_coverage.md](api_coverage.md)
- Evidence JSON under `evidence/ovirt-*.json`
- pytest: `tests/ovirt/`
