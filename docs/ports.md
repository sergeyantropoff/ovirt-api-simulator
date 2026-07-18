**Language / Язык:** [English](ports.md) | [Русский](ru/ports.md)

# Ports

Published host ports — **exactly two**, matching a typical Engine lab layout:

| Role | Container | Default host | Override env |
|------|-----------|--------------|--------------|
| Engine API + SSO | `443` | `443` | `OVIRT_ENGINE_PORT` |
| Web UI console | `5000` | `5000` | `OVIRT_UI_PORT` |

Examples:

```bash
https://127.0.0.1/ovirt-engine/api
http://127.0.0.1:5000/

# Optional override (only if the host already uses 443/5000):
# OVIRT_ENGINE_PORT=6443 OVIRT_UI_PORT=6080 docker compose up -d
```

Internal only (not published to the host): FastAPI `:8080`, PostgreSQL `:5432`.

The nginx `api-gateway` terminates TLS for Engine and proxies both listeners to
the simulator. Health checks work on either published port:

```bash
curl -skf https://127.0.0.1/health/ready
curl -sf http://127.0.0.1:5000/health/live
```
