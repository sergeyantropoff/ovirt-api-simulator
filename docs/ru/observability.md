**Language / Язык:** [English](../observability.md) | [Русский](observability.md)

# Наблюдаемость

## Health-эндпоинты

| Путь | Смысл |
|---|---|
| `/health/live` | Процесс запущен |
| `/health/ready` | БД доступна + миграции применены |

Оба доступны на симуляторе и через Compose gateway (любой опубликованный порт).

```bash
curl -skf https://127.0.0.1/health/ready
curl -sf http://127.0.0.1:5000/health/live
```

## Request ID

Заголовок `X-Request-ID` (настраивается через `REQUEST_ID_HEADER`) принимается и
эхоится там, где работает middleware.

## Логи

Compose:

```bash
make logs
docker compose logs -f simulator api-gateway
```

Helm (лейблы чарта: `app: ovirt-api-simulator`):

```bash
kubectl -n ovirt-sim logs -l app=ovirt-api-simulator -f
kubectl -n ovirt-sim logs -l app=ovirt-api-simulator-postgresql -f
```

## Evidence покрытия

- Покрытие pack: [api_coverage.md](api_coverage.md)
- Evidence JSON в `evidence/ovirt-*.json`
- pytest: `tests/ovirt/`
