**Language / Язык:** [English](authentication.md) | [Русский](ru/authentication.md)

# Authentication

The simulator implements Engine-style **HTTP Basic**, **SSO OAuth2** password
grant, and bearer tokens for subsequent API calls.

## Seeded principals

Password for all users: **`secret`**. Domain: **`internal`**.

| Principal | Typical role |
|---|---|
| `admin@internal` | SuperUser |
| `ops@internal` | lab operator |
| `developer@internal` | lab developer |
| `demo@internal` | demo user |

## HTTP Basic

```bash
curl -k -u 'admin@internal:secret' \
  -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms
```

## OAuth2 password grant

```bash
curl -k -X POST https://127.0.0.1/ovirt-engine/sso/oauth/token \
  -d 'grant_type=password&username=admin@internal&password=secret&scope=ovirt-app-api'
```

Response includes `access_token`, `token_type`, `scope`, and `exp`. Use the
token as a Bearer credential:

```bash
TOKEN=...  # access_token from the response
curl -k -H "Authorization: Bearer $TOKEN" \
  -H 'Accept: application/json' -H 'Version: 4' \
  https://127.0.0.1/ovirt-engine/api/vms
```

Related endpoints:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/ovirt-engine/sso/oauth/token` | Issue token |
| `GET` | `/ovirt-engine/sso/oauth/token-info` | Inspect token |
| `POST` | `/ovirt-engine/sso/oauth/revoke` | Revoke token |

## Errors

- Missing / invalid credentials → `401 Unauthorized`
- Wrong password → `401`
- Invalid or expired token → `401`
- Invalid OAuth scope → `400`

## Session cookie (lab)

After Basic authentication the simulator may establish a `JSESSIONID`-style
session cookie (or accept `Prefer: persistent-auth`). Prefer Bearer tokens for
automation; sessions are mainly for browser / Engine-client shaped flows.

## Web UI

The Auth drawer can issue a lab token for interactive catalog calls. See
[Web UI](web-ui.md).
