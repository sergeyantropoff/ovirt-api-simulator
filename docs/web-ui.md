**Language / Язык:** [English](web-ui.md) | [Русский](ru/web-ui.md)

# Web UI

Console URL (Compose default): [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

Drawer UX matches the other laboratory simulators in this family:

| Area | Purpose |
|---|---|
| Auth | Issue lab tokens / show principal |
| API catalog | Browse contract operations for the active series |
| Coverage | Pack / handler coverage summary |
| Help | Short operator notes |
| Data | Reseed `minimal` / `demo` |
| Environment | Active series, runtime hints, **Apply pack** hot-swap |

## Series hot-swap

From Environment (or UI API):

- `POST /ui/api/ovirt/contracts/activate` with `{"series":"4.4"}`
- `POST /ui/api/contract/apply?major=N`

This remounts the in-memory contract routes without rebuilding the image. A
process restart restores the cold-start `OVIRT_SERIES` value. See
[API versions](api-versions.md).

Branding uses oVirt blue `#0076B6` and charcoal `#1D2226`.

The UI talks to the same simulator process as the Engine API; only the published
listener differs ([ports.md](ports.md)). OpenAPI schema:
[http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs) (also on Engine port).
