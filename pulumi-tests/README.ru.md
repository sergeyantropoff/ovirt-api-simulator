**Language / Язык:** [English](README.md) | [Русский](README.ru.md)

# Лаборатория Pulumi: покрытие контрактов oVirt

**100% coverage** здесь — это **HTTP contract matrix**: каждая операция из
`contracts/ovirt/<series>/api.json` для **всех series packs** Engine, плюс
**синтетический HEAD** для каждого GET-пути (в contracts нет HEAD; Engine его
принимает). Это **не** число ресурсов Pulumi provider.

| Series | Операций (примерно) |
|--------|--------------------:|
| 3.0–3.6, 4.3–4.5, master | ~9 150 выполнений (ops из контрактов + HEAD) |

```bash
make test-pulumi-smoke   # выборка 3.6 + 4.5 (быстро)
make pulumi-tests        # полная матрица (alias: make test-pulumi)
```

Layer B (опционально): только smoke lifecycle провайдера — не выдавать за
полноту API.

Отчёты (в `reports/`):

- `pulumi-contract-coverage.html` — сводка (гистограмма методов:
  GET/PUT/POST/DELETE/HEAD)
- `pulumi-contract-coverage.json` — результат + `coverage`
  (`probed/declared`, `critical`)

Пример pass-строки:

```text
COVERAGE 9150/9150 (critical=0)
METHODS {"DELETE":1146,"GET":2314,"HEAD":2314,"POST":2230,"PUT":1146}
```

Фильтры:

```bash
OVIRT_SERIES_FILTER=4.5,3.6 make pulumi-tests
OVIRT_METHODS_FILTER=GET make pulumi-tests
SMOKE_ONLY=1 make test-pulumi-smoke
```

Все suites — **только в Docker** (lab compose сидит **minimal** seed).
Критерии pass:

- Маршрут Engine достижим и возвращает обработанный статус (`200`/`201`/`202`/`204`,
  `400`/`403`/`404`/`405`/`409`/`415`/`422`/`501`) — **не** `401` (после unload
  каждой series suite заново логинится) и не транспортную / `5xx` ошибку.
- Для `200`/`201`/`202` тело ответа должно быть непустым (HEAD исключён).
- Успешные **collection** GET должны возвращать **непустой** список с `id`
  (пустой `[]` — дыра seed/`ov_api_objects`, чинить данные, не skip).
- Полный прогон должен покрыть **GET, POST, PUT, DELETE и HEAD**; любые failures,
  отсутствующие методы или `probed != declared` валят suite (`critical=0`).
