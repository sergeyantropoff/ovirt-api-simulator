**Language / Язык:** [English](troubleshooting-clients.md) | [Русский](../ru/examples/troubleshooting-clients.md)

# Troubleshooting clients

## TLS verification failures

Expected with the Compose self-signed Engine cert. Disable verification in the
client (`verify=False`, `insecure`, `validate_certs: false`).

## HTTP 401

Confirm principal format `user@internal` and password `secret`. For OAuth,
include `scope=ovirt-app-api`.

## Wrong host / port

On Compose, Engine is **`443`** (HTTPS) and UI is **`5000`** (HTTP) by default.
Helm without a custom Ingress exposes FastAPI on **`8080`**. See
[ports.md](../ports.md) and [kubernetes.md](../kubernetes.md).

## Empty lists after seed

Wait for `/health/ready`. Lifespan auto-loads `minimal` unless the DB is already
`demo`. For density: `make seed-demo`.

## Proxy interference

IDE sandboxes often inject proxies that break local HTTPS. Unset proxy env vars
([overview.md](overview.md)).

## Version / XML surprises

Send `Version: 4` and `Accept: application/json` unless you intentionally test
v3 or XML.

## Wrong tool / suite

Prefer the snippets in this docs tree or the suites under `pulumi-tests/`.
