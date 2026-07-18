**Language / Язык:** [English](../faq.md) | [Русский](faq.md)

# FAQ

## Это настоящий oVirt Engine?

Нет. Это **лаборатория с полной API-поверхностью**: состояние в PostgreSQL,
ответы по форме контракта, без оркестрации гипервизоров.

## Какой series использовать?

По умолчанию **4.5**. Переключение через `OVIRT_SERIES` (Compose/Helm). См.
[api-versions.md](api-versions.md).

## Почему только два порта?

Engine API + SSO делят HTTPS; Web UI — отдельный HTTP listener. Так удобно
экспонировать Engine в лаборатории без публикации Postgres и внутреннего
FastAPI. Подробности: [ports.md](ports.md).

## Compose или Helm?

| Нужно | Использовать |
|---|---|
| Локальная разработка / CI на Docker | Compose |
| Установка в кластер | Helm ([kubernetes.md](kubernetes.md)) |

## Demo seed стёр мои ресурсы

Lifecycle-тесты и reseed очищают лабораторные таблицы. Перезагрузите:
`make seed-demo`.

## Можно ли направить Terraform / Ansible?

Да — HTTPS URL Engine и засеянные учётные данные. Предпочитайте нативные suites в
[`pulumi-tests/`](../../pulumi-tests/README.ru.md). Ожидайте лабораторные
ограничения (глубина policy, async workflows, реальные storage backends). См.
[examples/overview.md](examples/overview.md).

## Где Helm-чарт?

[`helm/ovirt-api-simulator`](../../helm/ovirt-api-simulator) — руководство в
[kubernetes.md](kubernetes.md).
