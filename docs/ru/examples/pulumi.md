**Language / Язык:** [English](../../examples/pulumi.md) | [Русский](pulumi.md)

# Pulumi

Лаборатория покрытия контрактов: [`pulumi-tests/`](../../../pulumi-tests/README.ru.md).

```bash
make up-local   # или: make up
make seed
make test-pulumi-smoke
make pulumi-tests        # alias: make test-pulumi
```

HTML-отчёт: `pulumi-tests/reports/pulumi-contract-coverage.html` (в gitignore).

## Последний проверенный результат (2026-07-18)

| Метрика | Значение |
|---|---:|
| total / passed / failed | **9150 / 9150 / 0** |
| методы | DELETE 1146 · GET 2314 · HEAD 2314 · POST 2230 · PUT 1146 |
| HTTP | 200: 6739 · 404: 1514 · 201: 864 · 400: 22 · 409: 11 |

Все series packs `3.0`–`3.6`, `4.3`–`4.5`, `master` — зелёные. См. также
[Тестирование](../testing.md).
