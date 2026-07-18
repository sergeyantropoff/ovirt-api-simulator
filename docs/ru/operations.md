**Language / Язык:** [English](../operations.md) | [Русский](operations.md)

# Эксплуатация

## Compose день за днём

```bash
make up            # сборка + старт + wait
make restart       # force recreate
make logs          # логи всех сервисов
make down          # остановка
make seed          # перезагрузка minimal
make seed-demo     # перезагрузка demo (~1000 ВМ)
make smoke         # Basic auth + список ВМ
```

## Миграции

Сервис Compose `migrate` / init-контейнер Helm запускает
`python -m app.db.migrate_cli` до готовности симулятора. Не направляйте клиенты
на Engine, пока `/health/ready` не успешен.

История схемы начинается с `001_ovirt_core.sql`. Если обновляетесь с более
ранней pre-release БД, пересоздайте том:

```bash
docker compose down -v
make up && make seed
```

## Reseed

Reseed **очищает** лабораторные таблицы. В общем CI предпочитайте `minimal`;
`demo` — когда нужна плотность.

```bash
make seed-demo
# или Web UI → Data → demo
```

## Смена series

**Cold start** — измените `OVIRT_SERIES` и пересоздайте контейнер симулятора:

```bash
OVIRT_SERIES=4.4 make restart
```

**Hot-swap** (in-memory, без пересборки) — Web UI Environment → Apply pack, или:

```bash
curl -s http://127.0.0.1:5000/ui/api/ovirt/contracts/activate \
  -H 'Content-Type: application/json' \
  -d '{"series":"4.4"}'
```

См. [Версии API](api-versions.md) и [Web UI](web-ui.md).

## Очистка клиентской лаборатории

```bash
make clean-test-resources
```

Удаляет ресурсы, созданные [`pulumi-tests/`](../../pulumi-tests/README.ru.md).

## Публикация в Docker Hub

`make release` собирает **runtime**-образ (production target — не локальный
bind-mounted образ `dev`) и публикует его в Docker Hub:

```bash
docker login   # once; account must own or can push to DOCKERHUB_USER
make release
```

Значения по умолчанию:

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `DOCKERHUB_USER` | `inecs` | Namespace/org в Docker Hub |
| `IMAGE_NAME` | `ovirt-api-simulator` | Имя репозитория |
| `VERSION` | from `pyproject.toml` | Тег образа |
| `PUSH_LATEST` | `1` | Также тегировать/пушить `:latest` |

Примеры:

```bash
make release
make release VERSION=0.2.0
make release DOCKERHUB_USER=myorg PUSH_LATEST=0
make release-build   # build/tag locally without pushing
```

Опубликованные теги:

- `inecs/ovirt-api-simulator:<version>`
- `inecs/ovirt-api-simulator:latest` (если не `PUSH_LATEST=0`)

## Быстрый старт с опубликованным compose-файлом

[`docker-compose.release.yml`](../../docker-compose.release.yml) подтягивает
runtime-образ из Hub и запускает PostgreSQL + migrate + simulator + Engine gateway:

```bash
docker compose -f docker-compose.release.yml up -d
docker compose -f docker-compose.release.yml run --rm --entrypoint python \
  simulator -m app.ovirt.seed_cli --profile minimal

curl -skf https://127.0.0.1/health/ready
```

Вспомогательные команды из git checkout:

```bash
make release-up
make release-seed PROFILE=minimal
# или: make release-seed PROFILE=demo
make release-down
```
