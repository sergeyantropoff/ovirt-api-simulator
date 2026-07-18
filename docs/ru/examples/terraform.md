**Language / Язык:** [English](../../examples/terraform.md) | [Русский](terraform.md)

# Terraform

Нативный suite (150 кейсов) находится в
[`pulumi-tests/terraform/`](../../../pulumi-tests/README.ru.md):

```bash
make up && make seed
make test-terraform-smoke
make test-terraform
```

Направляйте провайдеры на Engine HTTPS с лабораторными учётными данными и
отключайте проверку TLS для self-signed сертификата Compose.
