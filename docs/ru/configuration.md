**Language / Язык:** [English](../configuration.md) | [Русский](configuration.md)

# Конфигурация

Настройки приложения загружаются из окружения (см. `.env.example`).
Docker Compose подставляет многие из них для сервиса `simulator`.

## Основные

| Переменная | По умолчанию / пример | Назначение |
|---|---|---|
| `APP_HOST` | `0.0.0.0` | Адрес привязки |
| `APP_PORT` | `8080` | Внутренний порт FastAPI (не публичный Engine) |
| `DATABASE_URL` | `postgresql://ovirt:ovirt@postgres:5432/ovirt_simulator` | DSN asyncpg |
| `TEST_DATABASE_URL` | как выше | DSN для интеграционных тестов |
| `DB_POOL_MIN_SIZE` | `1` | Минимум пула |
| `DB_POOL_MAX_SIZE` | `10` | Максимум пула |
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| `REQUEST_ID_HEADER` | `X-Request-ID` | Заголовок корреляции запросов |

## Series Engine и seed

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `OVIRT_SERIES` | `4.5` | Контрактный pack при cold start (`3.0`–`3.6`, `4.3`–`4.5`, `master`) |
| `SEED_PROFILE` | `minimal` | Для seed CLI / Helm seed Job (`minimal` / `demo`) |

## Безопасность и задачи

| Переменная | Назначение |
|---|---|
| `TICKET_SIGNING_KEY` | Материал подписи лабораторных токенов (**меняйте вне игрушечных стендов**) |
| `TASK_WORKER_CONCURRENCY` | Число воркеров с арендой (1–32) |
| `TASK_LEASE_SECONDS` | Длительность аренды задач в PostgreSQL |
| `SIMULATION_TIME_SCALE` | Ускоряет длительность симулируемых jobs |

## Публикация портов на хост

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `OVIRT_ENGINE_PORT` | `443` | Host → gateway `:443` (Engine HTTPS) |
| `OVIRT_UI_PORT` | `5000` | Host → gateway `:5000` (Web UI) |

См. [Порты](ports.md).

## Compose

| Файл | Роль |
|---|---|
| `docker-compose.yml` | Dev-стек (сборка + bind mounts) |
| `docker-compose.release.yml` | Опубликованный образ Hub |
| `.env` / `.env.example` | Локальные переопределения |

Сервисы:

- **simulator** — FastAPI на внутреннем `8080`
- **api-gateway** — nginx, публикующий Engine + UI ([ports.md](ports.md))
- **postgres** — `postgres:17.5-bookworm` (host-порт по умолчанию не публикуется)
- **migrate** — one-shot миграции схемы

## Helm

См. [Kubernetes / Helm](kubernetes.md) и
[`helm/ovirt-api-simulator/values.yaml`](../../helm/ovirt-api-simulator/values.yaml).

| Value | Назначение |
|---|---|
| `image.repository` / `image.tag` | Образ контейнера |
| `config.ovirtSeries` | Pack series → env `OVIRT_SERIES` |
| `seed.profile` | `minimal` / `demo` |
| `postgresql.enabled` | Встроенная БД |
| `databaseUrl` | Внешний DSN, если встроенный Postgres выключен |
| `secrets.ticketSigningKey` | Нужно ротировать на общих кластерах |
| `service.port` | Порт ClusterIP (по умолчанию `8080`) |

`gateway.*` / `ingress.*` в `values.yaml` зарезервированы; чарт сейчас отдаёт
FastAPI напрямую (без nginx gateway как в Compose).

## Контрактные packs

Расположение: `contracts/ovirt/<series>/`.

В каждом series: `api.json`, `manifest.json` и `deltas.json`. Перегенерация:

```bash
make generate-packs
```
