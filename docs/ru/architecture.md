**Language / Язык:** [English](../architecture.md) | [Русский](architecture.md)

# Архитектура

## Цели

- Верная раскладка URL Engine (`/ovirt-engine/api`, SSO)
- Stateful-инвентарь в PostgreSQL
- Регистрация маршрутов по контрактным series packs
- Удобный лабораторный Web UI и детерминированные seeds

## Компоненты

```
clients / Web UI
       │
 api-gateway (nginx TLS + UI)
       │
  simulator (FastAPI :8080)
       │
   PostgreSQL
```

| Пакет | Ответственность |
|---|---|
| `app/ovirt/` | Маршруты Engine, SSO, seed, schema engine, versioning |
| `app/web/` | Консоль UI и UI API |
| `app/db/` | Миграции и пул соединений |
| `contracts/ovirt/` | Сгенерированные series packs |
| `docker/gateway/` | nginx listener'ы Engine + UI |

## Путь запроса

1. Клиент обращается к опубликованному порту Engine или UI.
2. Gateway проксирует на FastAPI.
3. Auth middleware разрешает Basic / Bearer.
4. Контрактный или semantic handler читает / меняет PostgreSQL.
5. Ответ сериализуется в JSON или XML.

## Связанное

- [Поверхность API](api-surface.md)
- [Профили seed](seed-profiles.md)
- [Эксплуатация](operations.md)
