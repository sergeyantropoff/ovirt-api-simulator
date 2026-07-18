**Language / Язык:** [English](../../examples/overview.md) | [Русский](overview.md)

# Клиенты и примеры

Используйте **inline-сниппеты** ниже и лабораторию Pulumi в
[`pulumi-tests/`](../../../pulumi-tests/README.ru.md).

## Base URL и учётные данные

| Параметр | Значение |
|---|---|
| Engine API | `https://127.0.0.1/ovirt-engine/api` |
| SSO token | `https://127.0.0.1/ovirt-engine/sso/oauth/token` |
| Web UI | `http://127.0.0.1:5000/` |
| Пользователь | `admin@internal` |
| Пароль | `secret` |

Отключите HTTP-прокси для локальных клиентов:

```bash
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
export NO_PROXY='*'
```

## Руководства

| Руководство | Фокус |
|---|---|
| [Python requests](python-requests.md) | Сырой HTTPS Basic / OAuth |
| [Ansible](ansible.md) | Модуль `uri` против Engine |
| [Terraform](terraform.md) | Заметки по IaC |
| [Pulumi](pulumi.md) | Полное покрытие контрактов + HTML-отчёт |
| [Troubleshooting clients](troubleshooting-clients.md) | Типичные сбои клиентов |

Предварительно: `make up && make seed` (или `make seed-demo`).
