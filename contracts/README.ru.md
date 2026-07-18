**Language / Язык:** [English](README.md) | [Русский](README.ru.md)

# Контрактные packs oVirt Engine

Генерируются `python tools/ovirt_api_inventory/generate_packs.py`
(цель Make: `make generate-packs`).

Каждый каталог `contracts/ovirt/<series>/` содержит:

| Файл | Роль |
|---|---|
| `api.json` | Объявленные операции Engine |
| `manifest.json` | Метаданные series и счётчики |
| `deltas.json` | Добавленные / удалённые ops относительно предыдущего series |

Индекс: [`ovirt/index.json`](ovirt/index.json).  
Документация: [Версии API](../docs/ru/api-versions.md),
[Покрытие API](../docs/ru/api_coverage.md).
