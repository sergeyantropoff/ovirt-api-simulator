**Language / Язык:** [English](../troubleshooting.md) | [Русский](troubleshooting.md)

# Устранение неполадок

## `/health/ready` возвращает 503

- Дождитесь завершения `migrate`: `docker compose ps`
- Проверьте Postgres: `docker compose logs postgres`
- Пересоздайте: `make restart`

## Ошибки TLS / сертификата

Compose использует self-signed сертификат на порту Engine. В лаборатории —
`curl -k` или флаги `insecure` / `verify=False` клиентов. См.
[Безопасность](security.md).

## Порт уже занят

Смените host-порты публикации:

```bash
OVIRT_ENGINE_PORT=7443 OVIRT_UI_PORT=7080 make up
```

## Пустой инвентарь / нет пользователей

Запустите seed:

```bash
make seed
# или
make seed-demo
```

## Неверный major API / нет полей

Задайте `Version: 4` (или `3`) либо используйте `/ovirt-engine/api/v4/...`.
Проверьте, что `OVIRT_SERIES` соответствует ожидаемому pack
([api-versions.md](api-versions.md)).

## Падения клиентских suites

Убедитесь, что стек поднят и засеян, затем сначала smoke:

```bash
make up && make seed && make smoke
make test-smoke-all
```

Отключите HTTP-прокси для локальных клиентов (`unset HTTP_PROXY HTTPS_PROXY …`).

## Всё ещё не ясно

Соберите:

```bash
docker compose ps
docker compose logs --tail=200 simulator api-gateway migrate
curl -sk -i https://127.0.0.1/health/ready
```
