**Language / Язык:** [English](api-versions.md) | [Русский](ru/api-versions.md)

# API versions (series packs)

The simulator ships Engine series packs under `contracts/ovirt/`:

| Series | API major | Cold-start env |
|---|---|---|
| `3.0` … `3.6` | v3 | `OVIRT_SERIES=3.6` |
| `4.3` | v4 | `OVIRT_SERIES=4.3` |
| `4.4` | v4 | `OVIRT_SERIES=4.4` |
| `4.5` | v4 | `OVIRT_SERIES=4.5` (default) |
| `master` | v4 | `OVIRT_SERIES=master` |

Operation counts and deltas: [API coverage](api_coverage.md).

## Selecting the API major (v3 / v4)

Clients can select the Engine API major in two ways:

1. **Path prefix:** `/ovirt-engine/api/v3/...` or `/ovirt-engine/api/v4/...`
2. **`Version` header:** `Version: 3` or `Version: 4` on `/ovirt-engine/api/...`

If neither is set, the default follows the active series (`3` for `3.x`, `4` for
`4.x` / `master`).

```bash
curl -k -u 'admin@internal:secret' \
  -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms

curl -k -u 'admin@internal:secret' \
  -H 'Accept: application/xml' \
  https://127.0.0.1/ovirt-engine/api/v3/vms
```

## Cold start

```bash
OVIRT_SERIES=4.4 docker compose up -d --build --wait
```

Helm:

```bash
--set config.ovirtSeries=3.6
```

## Hot-swap (in-memory)

Without recreating containers, activate another pack from the Web UI Environment
drawer or:

```bash
curl -s http://127.0.0.1:5000/ui/api/ovirt/contracts/activate \
  -H 'Content-Type: application/json' \
  -d '{"series":"4.4"}'
```

A process restart restores cold-start `OVIRT_SERIES`. Details: [Web UI](web-ui.md).

## Representations

Engine responses support **JSON** and **XML** via `Accept` /
`Content-Type` (`application/json`, `application/xml`).

## Pack layout

```
contracts/ovirt/<series>/
  api.json
  manifest.json
  deltas.json
```

Regenerate:

```bash
make generate-packs
```

Index: [`contracts/ovirt/index.json`](../contracts/ovirt/index.json).
