**Language / Язык:** [English](../../examples/troubleshooting-clients.md) | [Русский](troubleshooting-clients.md)

# Устранение неполадок клиентов

## Ошибки проверки TLS

Ожидаемо для self-signed сертификата Engine в Compose. Отключите проверку в
клиенте (`verify=False`, `insecure`, `validate_certs: false`).

## HTTP 401

Проверьте формат principal `user@internal` и пароль `secret`. Для OAuth укажите
`scope=ovirt-app-api`.

## Неверный host / порт

В Compose Engine по умолчанию на **`443`** (HTTPS), UI на **`5000`** (HTTP).
Helm без своего Ingress отдаёт FastAPI на **`8080`**. См.
[ports.md](../ports.md) и [kubernetes.md](../kubernetes.md).

## Пустые списки после seed

Дождитесь `/health/ready`. Lifespan сам загружает `minimal`, если БД ещё не
`demo`. Для плотности: `make seed-demo`.

## Помехи прокси

Песочницы IDE часто подставляют прокси, ломая локальный HTTPS. Сбросьте
переменные прокси ([overview.md](overview.md)).

## Сюрпризы Version / XML

Отправляйте `Version: 4` и `Accept: application/json`, если вы намеренно не
тестируете v3 или XML.

## Неверный инструмент / suite

Предпочитайте сниппеты в этой документации или suites в `pulumi-tests/`.
