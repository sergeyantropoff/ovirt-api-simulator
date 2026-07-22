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

## HTTP 401 / Web UI всё ещё показывает пользователя

Токен Engine SSO истёк или отозван (например после `demo/unload` / reseed).
В Web UI HTTP **401** очищает локальную сессию и показывает **Guest** в
шапке; войдите снова из Environment (`admin@internal` / `secret`).

## Ingress отдаёт брендированный HTML 404 / nginx 405 вместо fault Engine

Симулятор отвечает на ошибки API **fault** XML/JSON (`reason` / `detail`).
Если видите HTML «page not found» или plain nginx **405**, **Ingress /
reverse proxy** подменил тело ответа (часто через `custom-http-errors` у
ingress-nginx).

Исправление на Ingress для этого host (см.
`helm/ovirt-api-simulator/values-ingress-example.yaml`):

```yaml
annotations:
  nginx.ingress.kubernetes.io/proxy-intercept-errors: "false"
  nginx.ingress.kubernetes.io/custom-http-errors: "502,503"
```

Проверьте с `Accept: application/json`. Отсутствующий host должен выглядеть так:

```json
{"fault": {"reason": "NotFound", "detail": "No such host ('…')"}}
```

### Корректная authenticated mutation (стиль Engine)

Bearer (или Basic) и JSON-тело (не form-urlencoded):

```bash
# после POST /ovirt-engine/sso/oauth/token → access_token
TOKEN=…
curl -sk -X POST "https://HOST/ovirt-engine/api/vms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Version: 4" \
  -d '{"vm":{"name":"lab-vm","cluster":{"name":"Default"}}}'
```

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
