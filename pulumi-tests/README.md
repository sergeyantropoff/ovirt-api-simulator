**Language / Язык:** [English](README.md) | [Русский](README.ru.md)

# oVirt Pulumi contract-coverage lab

**100% coverage** here means the **HTTP contract matrix**: every operation
declared in `contracts/ovirt/<series>/api.json` for **all Engine series packs**,
plus a **synthetic HEAD** for each GET path (contracts omit HEAD; the Engine
accepts it). It is **not** a count of Pulumi provider resources.

| Series | Ops (approx.) |
|--------|--------------:|
| 3.0–3.6, 4.3–4.5, master | ~9 150 total executions (contract ops + HEAD) |

```bash
make test-pulumi-smoke   # 3.6 + 4.5 sample (fast)
make pulumi-tests        # full matrix (alias: make test-pulumi)
```

Layer B (optional): provider lifecycle smoke only — do not treat it as API
parity.

Reports (written under `reports/`):

- `pulumi-contract-coverage.html` — human-readable summary (method histogram
  includes GET/PUT/POST/DELETE/HEAD)
- `pulumi-contract-coverage.json` — machine-readable results + `coverage`
  (`probed/declared`, `critical`)

Pass line example:

```text
COVERAGE 9150/9150 (critical=0)
METHODS {"DELETE":1146,"GET":2314,"HEAD":2314,"POST":2230,"PUT":1146}
```

Optional filters:

```bash
OVIRT_SERIES_FILTER=4.5,3.6 make pulumi-tests
OVIRT_METHODS_FILTER=GET make pulumi-tests
SMOKE_ONLY=1 make test-pulumi-smoke
```

All suites run **only in Docker** (lab compose seeds **minimal** inventory).
Pass criteria:

- The Engine route is reachable and returns a handled status (`200`/`201`/`202`/`204`,
  `400`/`403`/`404`/`405`/`409`/`415`/`422`/`501`) — **not** `401` (the suite
  re-authenticates after each series unload) and not a transport/`5xx` failure.
- For `200`/`201`/`202` the response body must be non-empty (HEAD exempt).
- Successful **collection** GETs must return a **non-empty** list with `id`
  (empty `[]` is a seed/`ov_api_objects` gap — fix data, do not skip).
- Full runs must exercise **GET, POST, PUT, DELETE, and HEAD**; any failures,
  missing methods, or `probed != declared` fail the suite (`critical=0` required).
