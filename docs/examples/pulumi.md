**Language / Язык:** [English](pulumi.md) | [Русский](../ru/examples/pulumi.md)

# Pulumi

Contract-coverage lab under [`pulumi-tests/`](../../pulumi-tests/README.md).

```bash
make up-local   # or: make up
make seed
make test-pulumi-smoke
make pulumi-tests        # alias: make test-pulumi
```

HTML report: `pulumi-tests/reports/pulumi-contract-coverage.html` (gitignored).

## Last verified result (2026-07-18)

| Metric | Value |
|---|---:|
| total / passed / failed | **9150 / 9150 / 0** |
| methods | DELETE 1146 · GET 2314 · HEAD 2314 · POST 2230 · PUT 1146 |
| HTTP | 200: 6739 · 404: 1514 · 201: 864 · 400: 22 · 409: 11 |

All series packs `3.0`–`3.6`, `4.3`–`4.5`, `master` passed. See also
[Testing](../testing.md).
