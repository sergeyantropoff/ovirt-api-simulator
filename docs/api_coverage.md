**Language / Язык:** [English](api_coverage.md) | [Русский](ru/api_coverage.md)

# API coverage

Contract pack operation counts (from `contracts/ovirt/*/manifest.json`):

| Series | API | Operations | Deltas (added / removed) |
|---|---|---:|---|
| 3.0 | v3 | 468 | 468 / 0 |
| 3.1 | v3 | 498 | 30 / 0 |
| 3.2 | v3 | 506 | 8 / 0 |
| 3.3 | v3 | 576 | 70 / 0 |
| 3.4 | v3 | 598 | 22 / 0 |
| 3.5 | v3 | 640 | 42 / 0 |
| 3.6 | v3 | 684 | 44 / 0 |
| 4.3 | v4 | 706 | 364 / 342 |
| 4.4 | v4 | 720 | 14 / 0 |
| 4.5 | v4 | 720 | 0 / 0 |
| master | v4 | 720 | 0 / 0 |

Specialized handlers cover core inventory collections (VMs, disks, hosts,
networks, storage, jobs, …). Remaining pack operations are served by the schema
engine. See [API surface](api-surface.md).

## Pulumi contract matrix

`make pulumi-tests` executes **every** pack operation across all series, plus a
synthetic **HEAD** for each GET (~6 836 contract ops + ~2 314 HEAD = **9 150**
calls).

**Last verified (2026-07-18):** **9150 / 9150** passed — methods GET/POST/PUT/DELETE/HEAD;
HTTP mix 200/201/400/404/409; no `401` / `5xx`. See [Testing](testing.md) and
[`pulumi-tests/README.md`](../pulumi-tests/README.md).

> Measurable contract coverage for a laboratory simulator — not a claim that
> every Engine edge case behaves identically to production RHV/oVirt.
