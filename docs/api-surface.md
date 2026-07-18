**Language / Язык:** [English](api-surface.md) | [Русский](ru/api-surface.md)

# API surface

Entry points:

| Path | Role |
|---|---|
| `/ovirt-engine/api` | Engine REST root (v4 default on 4.x series) |
| `/ovirt-engine/api/v3` … `/v4` | Explicit API major |
| `/ovirt-engine/sso/oauth/*` | SSO OAuth2 |
| `/health/live`, `/health/ready` | Liveness / readiness |
| `/` (UI port) | Web console |

## Routing model

1. Contract routes from the active `contracts/ovirt/<series>` pack are registered
   as individual OpenAPI operations.
2. Specialized semantic handlers persist inventory mutations (VMs, disks, hosts,
   networks, storage domains, jobs, …).
3. A catch-all Engine router remains as a hidden fallback for remaining
   collections via the schema engine.

Packs live under [`contracts/ovirt/`](../contracts/README.md). Coverage table:
[api_coverage.md](api_coverage.md). Domain guides: [domains/](domains/README.md).

## Representations

Request/response bodies may be JSON or XML depending on `Accept` /
`Content-Type`. Prefer `Accept: application/json` for modern clients.
