**Language / Язык:** [English](README.md) | [Русский](README.ru.md)

# ovirt-api-simulator

Stateful-лабораторный симулятор **oVirt / RHV Engine REST API**. Нужен для
тестирования API-клиентов и инфраструктурных инструментов без реального Engine
и гипервизоров.

> **Только лаборатория.** Это не production Engine, гипервизоры не запускаются,
> в комплекте дефолтные учётные данные и self-signed TLS. Не выставляйте в
> недоверенные сети.

Симулятор работает на PostgreSQL, опирается на сгенерированные контрактные packs
Engine и предоставляет те же поверхности `/ovirt-engine/api` и SSO OAuth2, что и
oVirt Engine. Семантические обработчики сохраняют мутации; длительные операции
отслеживаются как Engine jobs.

## Быстрый старт (разработка из репозитория)

```bash
cp .env.example .env
make up
make seed          # или: make seed-small|seed-large|seed-big
```

| Поверхность | URL |
|---------|-----|
| Web UI консоль | http://127.0.0.1:5000 |
| Engine API | https://127.0.0.1/ovirt-engine/api |

По умолчанию публикуются ровно **два** host-порта: Engine `443` и UI `5000`.
Переопределите через `OVIRT_ENGINE_PORT` / `OVIRT_UI_PORT`, если они заняты.

**Учётные данные:** `admin@internal` / `secret`  
Также: `ops@internal`, `developer@internal`, `demo@internal` / `secret`

```bash
# OAuth password grant
curl -k -X POST https://127.0.0.1/ovirt-engine/sso/oauth/token \
  -d 'grant_type=password&username=admin@internal&password=secret&scope=ovirt-app-api'

# Список ВМ (HTTP Basic)
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms
```

## Быстрый старт (опубликованный образ)

Образ: [`inecs/ovirt-api-simulator`](https://hub.docker.com/r/inecs/ovirt-api-simulator)

Нужен checkout этого репозитория (TLS-сертификаты gateway и nginx-конфиг
монтируются с диска):

```bash
docker compose -f docker-compose.release.yml up -d
docker compose -f docker-compose.release.yml run --rm --entrypoint python \
  simulator -m app.ovirt.seed_cli --profile minimal

curl -skf https://127.0.0.1/health/ready
curl -k -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms
```

Или: `make release-up && make release-seed PROFILE=minimal`

| Поверхность | URL |
|---------|-----|
| Web UI консоль | http://127.0.0.1:5000 |
| Engine API | https://127.0.0.1/ovirt-engine/api |

**Учётные данные:** `admin@internal` / `secret`

## Возможности

- Реальные пути Engine: `/ovirt-engine/api`, `/ovirt-engine/api/v3|v4`, SSO OAuth2
- Представления XML + JSON (`Accept` / `Content-Type`)
- Series packs **3.0–3.6, 4.3–4.5, master** с дельтами операций
- Stateful-инвентарь в PostgreSQL + асинхронные jobs
- Профили seed: `minimal`, `small` (3h/50vm), `large` (10h/1000vm), `big` (30h/2000vm)
- Web UI с брендингом oVirt (`#0076B6` / charcoal `#1D2226`)
- Docker Compose + Helm
- API-тесты + [`pulumi-tests/`](pulumi-tests/README.ru.md) (покрытие контрактов Pulumi)

## Цели Make

```bash
make up
make up-local            # локальные порты через gitignored docker-compose.override.yml
make down-local          # остановить стек + удалить local override
make seed
make seed-large
make test-unit
make test-integration
make test-pulumi-smoke   # Pulumi smoke
make test-pulumi         # все series × все contract ops + HTML-отчёт
make pulumi-tests        # alias для test-pulumi
make test-all            # alias для test-pulumi
make push                # git add . → запрос commit → push origin + antropoff
# make push MSG="сообщение"      # сообщение без интерактива
```

Публикация в Docker Hub (нужен `docker login` владельца Hub; см.
[Эксплуатация](docs/ru/operations.md)):

```bash
make release                          # inecs/ovirt-api-simulator:<версия pyproject> + :latest
make release VERSION=0.2.0            # переопределить тег
make release-build                    # только build/tag, без push
make release-up && make release-seed  # запустить опубликованный стек локально
```

## Документация

| Руководство | Описание |
|---|---|
| [Быстрый старт](docs/ru/getting-started.md) | Первая лабораторная сессия |
| [Порты](docs/ru/ports.md) | Опубликованные порты Engine + UI |
| [Аутентификация](docs/ru/authentication.md) | Basic, OAuth2, сессии |
| [Версии API](docs/ru/api-versions.md) | Series packs и заголовок Version |
| [Конфигурация](docs/ru/configuration.md) | Окружение и Compose |
| [Профили seed](docs/ru/seed-profiles.md) | `minimal` / `small` / `large` / `big` |
| [Kubernetes / Helm](docs/ru/kubernetes.md) | Установка в кластер |
| [Полный индекс](docs/ru/README.md) | Все руководства |

Английские версии: [`README.md`](README.md) и [`docs/`](docs/README.md).
Переключайте язык с помощью заголовка на каждой странице.
