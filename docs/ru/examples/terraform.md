**Language / Язык:** [English](../../examples/terraform.md) | [Русский](terraform.md)

# Terraform

Настройте providers на Engine HTTPS с лабораторными учётными данными и
отключите проверку TLS для self-signed сертификата Compose.

```bash
make up-local   # или: make up
make seed
```

Отдельного Terraform suite в репозитории нет. Полное покрытие поверхности
Engine — матрица Pulumi:

```bash
make pulumi-tests
```

См. [Тестирование](../testing.md) и [`pulumi-tests/`](../../../pulumi-tests/README.ru.md).
**Последний прогон (2026-07-18):** **9150 / 9150** passed.
