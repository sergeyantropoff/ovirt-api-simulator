**Language / Язык:** [English](../kubernetes.md) | [Русский](kubernetes.md)

# Kubernetes / Helm

Установка чартом
[`helm/ovirt-api-simulator`](../../helm/ovirt-api-simulator).

Опубликованный образ (когда запушен):
[`inecs/ovirt-api-simulator`](https://hub.docker.com/r/inecs/ovirt-api-simulator)

## Что чарт ставит сейчас

| Компонент | Роль |
|---|---|
| **simulator** Deployment | FastAPI на порту контейнера `8080` |
| **Service** | ClusterIP → `8080` |
| **PostgreSQL** StatefulSet | Встроенный Postgres 17 (опционально) |
| **migrate** initContainer | Идемпотентные миграции схемы |
| **seed** Job (опционально) | Лабораторные данные `minimal` или `demo` |

> Compose публикует Engine HTTPS + UI через nginx `api-gateway`
> ([ports.md](ports.md)). Helm-чарт **пока не** включает этот gateway:
> ключи `gateway.*` / `ingress.*` в `values.yaml` зарезервированы и не
> используются. Доступ — к Service симулятора на `:8080` (port-forward или
> свой Ingress).

## Требования

- Kubernetes 1.27+ (или аналог)
- Helm 3.14+

## Установка

```bash
helm upgrade --install ovirt-sim ./helm/ovirt-api-simulator \
  -n ovirt-sim --create-namespace \
  --set image.repository=inecs/ovirt-api-simulator \
  --set image.tag=0.1.0 \
  --set config.ovirtSeries=4.5 \
  --set seed.profile=minimal \
  --set secrets.ticketSigningKey="$(openssl rand -hex 32)"
```

Для локально собранного образа задайте `image.repository` / `image.tag` под то,
что загружено в кластер.

Локальный render:

```bash
make helm-template
```

## Важные values

| Value | Назначение |
|---|---|
| `image.repository` / `image.tag` | Образ контейнера (по умолчанию `inecs/ovirt-api-simulator:0.1.0`) |
| `config.ovirtSeries` | Pack при cold start (`4.5`, `3.6`, …) |
| `seed.enabled` / `seed.profile` | Post-install seed Job |
| `postgresql.enabled` | Встроенная БД |
| `databaseUrl` | Внешний DSN при `postgresql.enabled=false` |
| `secrets.ticketSigningKey` | Ротировать на общих кластерах |
| `service.port` | Порт сервиса (по умолчанию `8080`) |

См. [`values.yaml`](../../helm/ovirt-api-simulator/values.yaml).

## Доступ

Port-forward Service симулятора:

```bash
kubectl -n ovirt-sim port-forward svc/<release>-ovirt-api-simulator 8080:8080
```

Далее:

| Поверхность | URL |
|---|---|
| Engine API | http://127.0.0.1:8080/ovirt-engine/api |
| SSO token | http://127.0.0.1:8080/ovirt-engine/sso/oauth/token |
| Web UI | http://127.0.0.1:8080/ |
| OpenAPI | http://127.0.0.1:8080/docs |

Логин по умолчанию после seed: `admin@internal` / `secret`.

## Ручной reseed

```bash
kubectl exec deploy/<release>-ovirt-api-simulator -- \
  python -m app.ovirt.seed_cli --profile demo
```
