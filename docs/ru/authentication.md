**Language / Язык:** [English](../authentication.md) | [Русский](authentication.md)

# Аутентификация

Симулятор реализует Engine-стиль **HTTP Basic**, **SSO OAuth2** password grant
и bearer-токены для последующих вызовов API.

## Засеянные учётные записи

Пароль для всех пользователей: **`secret`**. Домен: **`internal`**.

| Principal | Типичная роль |
|---|---|
| `admin@internal` | SuperUser |
| `ops@internal` | оператор лаборатории |
| `developer@internal` | разработчик лаборатории |
| `demo@internal` | демо-пользователь |

## HTTP Basic

```bash
curl -k -u 'admin@internal:secret' \
  -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms
```

## OAuth2 password grant

```bash
curl -k -X POST https://127.0.0.1/ovirt-engine/sso/oauth/token \
  -d 'grant_type=password&username=admin@internal&password=secret&scope=ovirt-app-api'
```

В ответе: `access_token`, `token_type`, `scope` и `exp`. Используйте токен как
Bearer:

```bash
TOKEN=...  # access_token из ответа
curl -k -H "Authorization: Bearer $TOKEN" \
  -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms
```

Связанные эндпоинты:

| Метод | Путь | Назначение |
|---|---|---|
| `POST` | `/ovirt-engine/sso/oauth/token` | Выдать токен |
| `GET` | `/ovirt-engine/sso/oauth/token-info` | Просмотреть токен |
| `POST` | `/ovirt-engine/sso/oauth/revoke` | Отозвать токен |

## Ошибки

- Нет / неверные учётные данные → `401 Unauthorized`
- Неверный пароль → `401`
- Недействительный или просроченный токен → `401`
- Неверный OAuth scope → `400`

## Session cookie (лаборатория)

После Basic-аутентификации симулятор может установить session cookie в стиле
`JSESSIONID` (или принять `Prefer: persistent-auth`). Для автоматизации
предпочитайте Bearer-токены; сессии в основном для браузера / Engine-подобных
клиентов.

## Web UI

Ящик Auth может выдать лабораторный токен для интерактивных вызовов каталога.
См. [Web UI](web-ui.md).
