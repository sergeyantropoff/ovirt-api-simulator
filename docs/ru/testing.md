**Language / Язык:** [English](../testing.md) | [Русский](testing.md)

# Тестирование

Как гонять лабораторную матрицу тестов и что показал последний полный прогон.

## Команды

| Цель | Что запускает |
|---|---|
| `make test` | Offline unit + contract (без живого Engine) |
| `make test-unit` | Unit-тесты в `tests/` |
| `make test-contract` | Проверки contract packs |
| `make test-integration` | Интеграция Engine на PostgreSQL |
| `make test-versions` | Seeded-ассерты по series packs |
| `make smoke` | Auth + список ВМ на поднятом стеке |
| `make test-pulumi-smoke` | Pulumi smoke (выборка 3.6 + 4.5) |
| `make pulumi-tests` | Полная Pulumi-матрица (все series × ops + HEAD) |
| `make lint` / CI critical lint | Ruff (в CI только `E9,F63,F7,F82`) |
| `make helm-template` | Рендер Helm-чарта |

Полный локальный gate перед релизом:

```bash
make up-local   # или make up
make seed
make smoke
make test
make test-unit
make test-contract
make test-integration
make test-versions
make pulumi-tests
```

HTML-отчёт Pulumi: `pulumi-tests/reports/pulumi-contract-coverage.html`  
(в gitignore — пересобирается каждым прогоном). Подробности:
[`pulumi-tests/README.ru.md`](../../pulumi-tests/README.ru.md).

## Последний полный прогон

**Дата:** 2026-07-18  

| Suite | Результат | Примечание |
|---|---|---|
| `helm lint` / `helm-template` | PASS | |
| `make test` (offline) | PASS | |
| `make test-unit` | PASS | |
| `make test-contract` | PASS | |
| `make up-local` / `seed` / `smoke` | PASS | |
| `make test-integration` | PASS | |
| `make test-versions` | PASS | |
| CI critical lint | PASS | |
| `make pulumi-tests` | PASS | **9150 / 9150** |

### Матрица Pulumi

| Метрика | Значение |
|---|---:|
| total | 9150 |
| passed | 9150 |
| failed | 0 |
| skipped | 0 |

**Методы:** DELETE 1146 · GET 2314 · HEAD 2314 · POST 2230 · PUT 1146  

**HTTP:** 200: 6739 · 404: 1514 · 201: 864 · 400: 22 · 409: 11  
(без `401`, без `5xx`)

Series: `3.0`–`3.6`, `4.3`–`4.5`, `master` (все зелёные).

> Pass значит: каждый contract-маршрут достижим с обработанным статусом Engine и
> проверками тела — не побитовая идентичность production RHV.
