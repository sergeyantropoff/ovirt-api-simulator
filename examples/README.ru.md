**Language / Язык:** [English](README.md) | [Русский](README.ru.md)

# Примеры

| Путь | Что |
|---|---|
| [`docs/examples/`](../docs/ru/examples/overview.md) | Сниппеты curl / Python / Ansible / Terraform |
| [`pulumi-tests/`](../pulumi-tests/README.ru.md) | Pulumi-покрытие контрактов по всем series Engine |

```bash
make up-local   # или: make up
make seed
make pulumi-tests
# отчёт: pulumi-tests/reports/pulumi-contract-coverage.html
```

**Последний прогон (2026-07-18):** Pulumi **9150 / 9150** passed (GET/POST/PUT/DELETE/HEAD).  
См. [Тестирование](../docs/ru/testing.md).
