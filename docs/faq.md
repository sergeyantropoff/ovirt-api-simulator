**Language / Язык:** [English](faq.md) | [Русский](ru/faq.md)

# FAQ

## Is this a real oVirt Engine?

No. It is a **surface-complete API laboratory**: PostgreSQL-backed state,
contract-shaped responses, no hypervisor orchestration.

## Which series should I use?

Default **4.5**. Switch with `OVIRT_SERIES` (Compose/Helm). See
[api-versions.md](api-versions.md).

## Why only two ports?

Engine API + SSO share HTTPS; the Web UI uses a separate HTTP listener. That
matches how labs typically expose Engine without publishing Postgres or the
internal FastAPI port. Details: [ports.md](ports.md).

## Compose vs Helm?

| Need | Use |
|---|---|
| Local hack / CI on Docker | Compose |
| Cluster install | Helm ([kubernetes.md](kubernetes.md)) |

## Demo seed wiped my resources

Lifecycle tests and reseed truncate lab tables. Reload with `make seed-demo`.

## Can I point Terraform / Ansible at it?

Yes — use Engine HTTPS URL and seeded credentials. Prefer the native suites under
[`pulumi-tests/`](../pulumi-tests/README.md). Expect lab limitations (policy
depth, async workflows, real storage backends). See
[examples/overview.md](examples/overview.md).

## Where is the Helm chart?

[`helm/ovirt-api-simulator`](../helm/ovirt-api-simulator) — guide in
[kubernetes.md](kubernetes.md).
