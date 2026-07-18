**Language / Язык:** [English](../ports.md) | [Русский](ports.md)

# Порты

Опубликованные host-порты — ровно **два**, как у типичного Engine-стенда:

| Роль | Контейнер | Host по умолчанию | Переопределение |
|------|-----------|-------------------|-----------------|
| Engine API + SSO | `443` | `443` | `OVIRT_ENGINE_PORT` |
| Web UI консоль | `5000` | `5000` | `OVIRT_UI_PORT` |

Примеры:

```bash
https://127.0.0.1/ovirt-engine/api
http://127.0.0.1:5000/

# Опциональный override (только если на хосте уже заняты 443/5000):
# OVIRT_ENGINE_PORT=6443 OVIRT_UI_PORT=6080 docker compose up -d
```

Только внутри сети (не публикуются на хост): FastAPI `:8080`, PostgreSQL `:5432`.

Nginx `api-gateway` завершает TLS для Engine и проксирует оба listener'а на
симулятор. Health-проверки работают на любом опубликованном порту:

```bash
curl -skf https://127.0.0.1/health/ready
curl -sf http://127.0.0.1:5000/health/live
```
