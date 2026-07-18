**Language / Язык:** [English](web-ui.md) | [Русский](ru/web-ui.md)

# Web UI

Interactive console for browsing Engine contract operations, issuing lab tokens,
sending Try-it requests, and managing seed data.

Compose default URL: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)  
(With `make up-local`, use the local UI port from your `.env`, e.g. `6080` / `7080`.)

![Console](images/web-ui/console.png)

## Workspace

| Area | Purpose |
|---|---|
| Endpoint picker | Searchable catalog of contract paths (Engine series pack) |
| Method tabs | `GET` / `POST` / `PUT` / `DELETE` for the selected path |
| Request body | Engine-shaped JSON sample for create/update/action |
| Params | Flattened path + body fields for quick edits |
| Response | Status + JSON tree for the last call |
| History | Recent Try-it requests (replay / restore) |

![Endpoints drawer](images/web-ui/endpoints.png)

![POST /vms with Engine-shaped body](images/web-ui/request-body.png)

![Request parameters](images/web-ui/request-params.png)

Request bodies follow the real Engine convention (root-wrapped entity or
`action`). Samples include nested refs (`cluster`, `template`, CPU topology,
storage domains) aligned with the seeded lab inventory — not a one-field stub.

![History](images/web-ui/history.png)

## Drawers

| Drawer | Purpose |
|---|---|
| Authentication | Engine SSO password grant / paste Bearer token |
| API catalog | Browse series packs; **Apply as runtime** hot-swap |
| Help → Compatibility | Declared / implemented / verified surface summary |
| Data | Reseed `minimal` / `small` / `large` / `big` |
| Environment | Runtime series + datacenter inventory overview |

![Authentication](images/web-ui/authentication.png)

Default lab principals: `admin@internal`, `ops@internal`, `developer@internal`,
`demo@internal` / `secret`. Scope: `ovirt-app-api`.

![API catalog](images/web-ui/api-catalog.png)

![Help / compatibility](images/web-ui/help-compatibility.png)

![Data presets](images/web-ui/data.png)

![Environment](images/web-ui/environment.png)

## Series hot-swap

From **API catalog** → **Apply as runtime** (or UI API):

- `POST /ui/api/ovirt/contracts/activate` with `{"series":"4.4"}`
- `POST /ui/api/contract/apply?major=N`

This remounts the in-memory contract routes without rebuilding the image. A
process restart restores the cold-start `OVIRT_SERIES` value. See
[API versions](api-versions.md).

## Notes

- Branding uses oVirt blue `#0076B6` and charcoal `#1D2226`.
- The UI talks to the same simulator process as the Engine API; only the
  published listener differs ([ports.md](ports.md)).
- OpenAPI schema: [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs)
  (also available on the Engine HTTPS port).
