**Language / Язык:** [English](overview.md) | [Русский](../ru/examples/overview.md)

# Clients & examples

Use the **inline snippets** below and the Pulumi contract-coverage lab under
[`pulumi-tests/`](../../pulumi-tests/README.md).

## Base URL and credentials

| Setting | Value |
|---|---|
| Engine API | `https://127.0.0.1/ovirt-engine/api` |
| SSO token | `https://127.0.0.1/ovirt-engine/sso/oauth/token` |
| Web UI | `http://127.0.0.1:5000/` |
| User | `admin@internal` |
| Password | `secret` |

Disable HTTP proxies for local clients:

```bash
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
export NO_PROXY='*'
```

## Guides

| Guide | Focus |
|---|---|
| [Python requests](python-requests.md) | Raw HTTPS Basic / OAuth |
| [Ansible](ansible.md) | `uri` module against Engine |
| [Terraform](terraform.md) | IaC notes |
| [Pulumi](pulumi.md) | Full contract coverage + HTML report |
| [Troubleshooting clients](troubleshooting-clients.md) | Common client failures |

Prerequisites: `make up && make seed` (or `make seed-demo`).
