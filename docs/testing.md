**Language / Язык:** [English](testing.md) | [Русский](ru/testing.md)

# Testing

How to run the laboratory test matrix and what the last full run reported.

## Commands

| Target | What it runs |
|---|---|
| `make test` | Offline unit + contract (no live Engine) |
| `make test-unit` | Unit tests under `tests/` |
| `make test-contract` | Contract-pack checks |
| `make test-integration` | PostgreSQL-backed Engine integration |
| `make test-versions` | Seeded assertions across series packs |
| `make smoke` | Auth + list VMs against the running stack |
| `make test-pulumi-smoke` | Pulumi smoke (3.6 + 4.5 sample) |
| `make pulumi-tests` | Full Pulumi contract matrix (all series × ops + HEAD) |
| `make lint` / CI critical lint | Ruff (CI uses `E9,F63,F7,F82` only) |
| `make helm-template` | Render Helm chart |

Full local gate used before release:

```bash
make up-local   # or make up
make seed
make smoke
make test
make test-unit
make test-contract
make test-integration
make test-versions
make pulumi-tests
```

Pulumi HTML report: `pulumi-tests/reports/pulumi-contract-coverage.html`  
(gitignored — regenerated each run). Details: [`pulumi-tests/README.md`](../pulumi-tests/README.md).

## Last verified full run

**Date:** 2026-07-18  

| Suite | Result | Notes |
|---|---|---|
| `helm lint` / `helm-template` | PASS | |
| `make test` (offline) | PASS | |
| `make test-unit` | PASS | |
| `make test-contract` | PASS | |
| `make up-local` / `seed` / `smoke` | PASS | |
| `make test-integration` | PASS | |
| `make test-versions` | PASS | |
| CI critical lint | PASS | |
| `make pulumi-tests` | PASS | **9150 / 9150** |

### Pulumi contract matrix

| Metric | Value |
|---|---:|
| total | 9150 |
| passed | 9150 |
| failed | 0 |
| skipped | 0 |

**Methods:** DELETE 1146 · GET 2314 · HEAD 2314 · POST 2230 · PUT 1146  

**HTTP status histogram:** 200: 6739 · 404: 1514 · 201: 864 · 400: 22 · 409: 11  
(no `401`, no `5xx`)

Series covered: `3.0`–`3.6`, `4.3`–`4.5`, `master` (all green).

> Pass means every contract route is reachable with a handled Engine status and
> required body checks — not bit-identical behaviour to production RHV hardware.
