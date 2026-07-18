**Language / Язык:** [English](../api-surface.md) | [Русский](api-surface.md)

# Поверхность API

Точки входа:

| Путь | Роль |
|---|---|
| `/ovirt-engine/api` | Корень Engine REST (v4 по умолчанию на series 4.x) |
| `/ovirt-engine/api/v3` … `/v4` | Явный major API |
| `/ovirt-engine/sso/oauth/*` | SSO OAuth2 |
| `/health/live`, `/health/ready` | Liveness / readiness |
| `/` (порт UI) | Web-консоль |

## Модель маршрутизации

1. Контрактные маршруты активного pack `contracts/ovirt/<series>` регистрируются
   как отдельные OpenAPI-операции.
2. Специализированные semantic handlers сохраняют мутации инвентаря (ВМ, диски,
   хосты, сети, storage domains, jobs, …).
3. Catch-all роутер Engine остаётся скрытым fallback для остальных коллекций
   через schema engine.

Packs: [`contracts/ovirt/`](../../contracts/README.ru.md). Таблица покрытия:
[api_coverage.md](api_coverage.md). Домены: [domains/](domains/README.md).

## Представления

Тела запросов/ответов — JSON или XML в зависимости от `Accept` /
`Content-Type`. Для современных клиентов предпочитайте
`Accept: application/json`.
