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
