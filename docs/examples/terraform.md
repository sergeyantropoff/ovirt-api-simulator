**Language / Язык:** [English](terraform.md) | [Русский](../ru/examples/terraform.md)

# Terraform

Native suite (150 cases) lives under
[`pulumi-tests/terraform/`](../../pulumi-tests/README.md):

```bash
make up && make seed
make test-terraform-smoke
make test-terraform
```

Configure providers against Engine HTTPS with lab credentials and disable TLS
verification for the Compose self-signed certificate.
