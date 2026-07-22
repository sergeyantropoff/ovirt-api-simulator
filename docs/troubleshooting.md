**Language / Язык:** [English](troubleshooting.md) | [Русский](ru/troubleshooting.md)

# Troubleshooting

## `/health/ready` returns 503

- Wait for `migrate` to finish: `docker compose ps`
- Check Postgres: `docker compose logs postgres`
- Recreate: `make restart`

## TLS / certificate errors

Compose uses a self-signed cert on the Engine port. Use `curl -k` or client
`insecure` / `verify=False` flags in labs. See [Security](security.md).

## Port already in use

Change host publish ports:

```bash
OVIRT_ENGINE_PORT=7443 OVIRT_UI_PORT=7080 make up
```

## Empty inventory / missing users

Run seed:

```bash
make seed
# or
make seed-demo
```

## Wrong API major / missing fields

Set `Version: 4` (or `3`) or use `/ovirt-engine/api/v4/...`. Confirm
`OVIRT_SERIES` matches the pack you expect ([api-versions.md](api-versions.md)).

## HTTP 401 / Web UI still shows signed-in user

Engine SSO token expired or was revoked (e.g. after `demo/unload` / reseed).
In the Web UI, HTTP **401** clears the local session and shows **Guest** in the
header; sign in again from Environment (`admin@internal` / `secret`).

## Ingress returns branded HTML 404 / nginx 405 instead of Engine fault

The simulator answers API errors as Engine **fault** XML/JSON
(`reason` / `detail`). If you see a site HTML “page not found” or plain nginx
**405** page, the **Ingress / reverse proxy** replaced the upstream body (often
via `custom-http-errors` on the ingress-nginx controller).

Fix on the Ingress for this host (see
`helm/ovirt-api-simulator/values-ingress-example.yaml`):

```yaml
annotations:
  nginx.ingress.kubernetes.io/proxy-intercept-errors: "false"
  nginx.ingress.kubernetes.io/custom-http-errors: "502,503"
```

Then re-check with `Accept: application/json`. A missing host should look like:

```json
{"fault": {"reason": "NotFound", "detail": "No such host ('…')"}}
```

### Correct authenticated mutation (Engine-style)

Use Bearer (or Basic) auth and JSON body (not form-urlencoded):

```bash
# after POST /ovirt-engine/sso/oauth/token → access_token
TOKEN=…
curl -sk -X POST "https://HOST/ovirt-engine/api/vms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Version: 4" \
  -d '{"vm":{"name":"lab-vm","cluster":{"name":"Default"}}}'
```

## Client suite failures

Ensure the stack is up and seeded, then run smoke first:

```bash
make up && make seed && make smoke
make test-smoke-all
```

Disable HTTP proxies for local multi-hop clients (`unset HTTP_PROXY HTTPS_PROXY …`).

## Still stuck

Collect:

```bash
docker compose ps
docker compose logs --tail=200 simulator api-gateway migrate
curl -sk -i https://127.0.0.1/health/ready
```
