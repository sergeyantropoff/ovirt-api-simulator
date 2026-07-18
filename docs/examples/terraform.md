**Language / Язык:** [English](terraform.md) | [Русский](../ru/examples/terraform.md)

# Terraform

Configure providers against Engine HTTPS with lab credentials and disable TLS
verification for the Compose self-signed certificate.

```bash
make up-local   # or: make up
make seed
```

There is no separate Terraform test suite in this repo. Use the Pulumi contract
matrix for full Engine surface coverage:

```bash
make pulumi-tests
```

See [Testing](../testing.md) and [`pulumi-tests/`](../../pulumi-tests/README.md).
**Last verified (2026-07-18):** **9150 / 9150** passed.
