**Language / Язык:** [English](README.md) | [Русский](README.ru.md)

# oVirt Pulumi contract-coverage lab

Pulumi Automation API suite that exercises **every operation** declared in
`contracts/ovirt/<series>/api.json` across **all Engine series packs**, plus a
**synthetic HEAD** request for each GET path (contracts omit HEAD; the Engine
accepts it).

| Series | Ops (approx.) |
|--------|--------------:|
| 3.0–3.6, 4.3–4.5, master | ~9 150 total executions (contract ops + HEAD) |

```bash
make test-pulumi-smoke   # 3.6 + 4.5 sample (fast)
make pulumi-tests        # full matrix (alias: make test-pulumi)
```

Reports (written under `reports/`):

- `pulumi-contract-coverage.html` — human-readable summary (includes methods histogram)
- `pulumi-contract-coverage.json` — machine-readable results

Optional filters:

```bash
OVIRT_SERIES_FILTER=4.5,3.6 make pulumi-tests
OVIRT_METHODS_FILTER=GET make pulumi-tests
SMOKE_ONLY=1 make test-pulumi-smoke
```

All suites run **only in Docker**. Pass criteria:

- The Engine route is reachable and returns a handled status (`200`/`201`/`202`/`204`,
  `400`/`403`/`404`/`405`/`409`/`415`/`422`/`501`) — **not** `401` (the suite
  re-authenticates after each series unload) and not a transport/`5xx` failure.
- For `200`/`201`/`202` the response body must be non-empty (HEAD exempt).
- Full runs must exercise **GET, POST, PUT, DELETE, and HEAD**; any failures or
  missing methods fail the suite.
