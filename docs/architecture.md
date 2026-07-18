**Language / Язык:** [English](architecture.md) | [Русский](ru/architecture.md)

# Architecture

## Goals

- Faithful Engine URL layout (`/ovirt-engine/api`, SSO)
- Stateful inventory in PostgreSQL
- Contract-driven route registration per series pack
- Lab-friendly Web UI and deterministic seeds

## Components

```
clients / Web UI
       │
 api-gateway (nginx TLS + UI)
       │
  simulator (FastAPI :8080)
       │
   PostgreSQL
```

| Package | Responsibility |
|---|---|
| `app/ovirt/` | Engine routes, SSO, seed, schema engine, versioning |
| `app/web/` | Console UI and UI API |
| `app/db/` | Migrations and connection pool |
| `contracts/ovirt/` | Generated series packs |
| `docker/gateway/` | nginx Engine + UI listeners |

## Request path

1. Client hits published Engine or UI port.
2. Gateway proxies to FastAPI.
3. Auth middleware resolves Basic / Bearer.
4. Contract or semantic handler mutates / reads PostgreSQL.
5. Response serialized as JSON or XML.

## Related

- [API surface](api-surface.md)
- [Seed profiles](seed-profiles.md)
- [Operations](operations.md)
