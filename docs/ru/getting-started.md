**Language / Язык:** [English](../getting-started.md) | [Русский](getting-started.md)

# Быстрый старт

Поднимите локальную Engine-лабораторию, аутентифицируйтесь и выполните первый
запрос к симулятору.

## Требования

- Docker и Docker Compose
- `make` (опционально, но используется в документированных командах)

Python, линтеры и тесты запускаются **внутри** контейнеров. Локальный Python
toolchain для повседневной работы не нужен.

## Выберите путь

| Путь | Когда использовать |
|---|---|
| [Разработка из репозитория](#1a-разработка-из-репозитория) | Вклад в код / bind-mount исходников |
| [Опубликованный образ](#1b-опубликованный-образ) | Быстрый стенд с образом Hub |
| [Helm / Kubernetes](kubernetes.md) | Установка в кластер (nginx gateway пока нет) |

## 1a. Разработка из репозитория

```bash
cp .env.example .env
make install
make up
make seed
```

| Host-порт | Сервис |
|---|---|
| `443` | Engine API + SSO (HTTPS) |
| `5000` | Web UI консоль (HTTP) |

Публикуются только эти два порта. Внутренний FastAPI слушает `:8080` в сети
Compose. См. [Порты](ports.md).

Миграции применяются автоматически через one-shot сервис `migrate`.

## 1b. Опубликованный образ

Использует [`docker-compose.release.yml`](../../docker-compose.release.yml) —
PostgreSQL + migrate + simulator + Engine gateway из runtime-образа Hub:

```bash
docker compose -f docker-compose.release.yml pull
docker compose -f docker-compose.release.yml up -d
docker compose -f docker-compose.release.yml run --rm --entrypoint python \
  simulator -m app.ovirt.seed_cli --profile minimal
```

При необходимости переопределите тег через `IMAGE_TAG=0.1.0`. Из git checkout:

```bash
make release-up
make release-seed PROFILE=minimal
```

## 2. Дождитесь готовности

```bash
curl -skf https://127.0.0.1/health/ready
curl -sf http://127.0.0.1:5000/health/live
```

`/health/ready` возвращает HTTP 503, пока PostgreSQL недоступен **или** не
применена последняя упакованная миграция.

## 3. Загрузите профиль seed

```bash
make seed          # минимальная лаборатория
# или
make seed-demo     # ~1000 ВМ
```

См. [Профили seed](seed-profiles.md).

## 4. Аутентификация и список ВМ

```bash
curl -k -u 'admin@internal:secret' \
  -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms
```

Или получите OAuth-токен:

```bash
curl -k -X POST https://127.0.0.1/ovirt-engine/sso/oauth/token \
  -d 'grant_type=password&username=admin@internal&password=secret&scope=ovirt-app-api'
```

Подробности: [Аутентификация](authentication.md).

## 5. Откройте Web UI

Откройте [http://127.0.0.1:5000/](http://127.0.0.1:5000/) — ящик Auth, каталог
API, покрытие и управление reseed в Data. См. [Web UI](web-ui.md).

## Дальше

- [Версии API](api-versions.md) — переключение series packs (`OVIRT_SERIES`)
- [Клиенты и примеры](examples/overview.md) — cookbook'и
- [Домены](domains/README.md) — ВМ, storage, сети
- [Устранение неполадок](troubleshooting.md) — типичные сбои
