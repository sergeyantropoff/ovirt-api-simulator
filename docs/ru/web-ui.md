**Language / Язык:** [English](../web-ui.md) | [Русский](web-ui.md)

# Web UI

URL консоли (Compose по умолчанию): [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

UX ящиков совпадает с другими лабораторными симуляторами этого семейства:

| Область | Назначение |
|---|---|
| Auth | Выдача лабораторных токенов / показ principal |
| API catalog | Обзор операций контракта активного series |
| Coverage | Сводка покрытия pack / handlers |
| Help | Краткие заметки оператора |
| Data | Reseed `minimal` / `demo` |
| Environment | Активный series, runtime-подсказки, hot-swap **Apply pack** |

## Hot-swap series

Из Environment (или UI API):

- `POST /ui/api/ovirt/contracts/activate` с `{"series":"4.4"}`
- `POST /ui/api/contract/apply?major=N`

Перемонтирует in-memory контрактные маршруты без пересборки образа. Рестарт
процесса возвращает cold-start значение `OVIRT_SERIES`. См.
[Версии API](api-versions.md).

Брендинг: oVirt blue `#0076B6` и charcoal `#1D2226`.

UI обращается к тому же процессу симулятора, что и Engine API; отличается только
опубликованный listener ([ports.md](ports.md)). Схема OpenAPI:
[http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs) (также на порту Engine).
