**Language / Язык:** [English](README.md) | [Русский](README.ru.md)

# Examples

| Path | What |
|---|---|
| [`docs/examples/`](../docs/examples/overview.md) | curl / Python / Ansible / Terraform snippets |
| [`pulumi-tests/`](../pulumi-tests/README.md) | Pulumi contract coverage across all Engine series |

```bash
make up-local   # or: make up
make seed
make pulumi-tests
# report: pulumi-tests/reports/pulumi-contract-coverage.html
```

**Last verified (2026-07-18):** Pulumi **9150 / 9150** passed (GET/POST/PUT/DELETE/HEAD).  
See [Testing](../docs/testing.md).
