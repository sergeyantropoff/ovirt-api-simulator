**Language / Язык:** [English](../api-versions.md) | [Русский](api-versions.md)

# Версии API (series packs)

Симулятор поставляет Engine series packs в `contracts/ovirt/`:

| Series | Major API | Env при cold start |
|---|---|---|
| `3.0` … `3.6` | v3 | `OVIRT_SERIES=3.6` |
| `4.3` | v4 | `OVIRT_SERIES=4.3` |
| `4.4` | v4 | `OVIRT_SERIES=4.4` |
| `4.5` | v4 | `OVIRT_SERIES=4.5` (по умолчанию) |
| `master` | v4 | `OVIRT_SERIES=master` |

Числа операций и дельты: [Покрытие API](api_coverage.md).

## Выбор major API (v3 / v4)

Клиенты выбирают major Engine API двумя способами:

1. **Префикс пути:** `/ovirt-engine/api/v3/...` или `/ovirt-engine/api/v4/...`
2. **Заголовок `Version`:** `Version: 3` или `Version: 4` на `/ovirt-engine/api/...`

Если ничего не задано, default следует активному series (`3` для `3.x`, `4` для
`4.x` / `master`).

```bash
curl -k -u 'admin@internal:secret' \
  -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms

curl -k -u 'admin@internal:secret' \
  -H 'Accept: application/xml' \
  https://127.0.0.1/ovirt-engine/api/v3/vms
```

## Cold start

```bash
OVIRT_SERIES=4.4 docker compose up -d --build --wait
```

Helm:

```bash
--set config.ovirtSeries=3.6
```

## Hot-swap (in-memory)

Без пересоздания контейнеров активируйте другой pack из ящика Environment в
Web UI или:

```bash
curl -s http://127.0.0.1:5000/ui/api/ovirt/contracts/activate \
  -H 'Content-Type: application/json' \
  -d '{"series":"4.4"}'
```

Рестарт процесса возвращает cold-start `OVIRT_SERIES`. Подробности:
[Web UI](web-ui.md).

## Представления

Ответы Engine поддерживают **JSON** и **XML** через `Accept` /
`Content-Type` (`application/json`, `application/xml`).

## Структура pack

```
contracts/ovirt/<series>/
  api.json
  manifest.json
  deltas.json
```

Перегенерация:

```bash
make generate-packs
```

Индекс: [`contracts/ovirt/index.json`](../../contracts/ovirt/index.json).
