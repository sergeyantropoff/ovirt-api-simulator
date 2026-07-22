**Language / Язык:** [English](kubernetes.md) | [Русский](ru/kubernetes.md)

# Kubernetes / Helm

Deploy with the chart in
[`helm/ovirt-api-simulator`](../helm/ovirt-api-simulator).

Published image (when pushed):
[`inecs/ovirt-api-simulator`](https://hub.docker.com/r/inecs/ovirt-api-simulator)

## What the chart installs today

| Component | Role |
|---|---|
| **simulator** Deployment | FastAPI on container port `8080` |
| **Service** | ClusterIP → `8080` |
| **PostgreSQL** StatefulSet | Bundled Postgres 17 (optional) |
| **migrate** initContainer | Idempotent schema migrations |
| **seed** Job (optional) | `minimal` or `demo` lab data |

> The Compose stack publishes Engine HTTPS + UI via nginx `api-gateway`
> ([ports.md](ports.md)). The Helm chart serves the simulator Service on `:8080`.
> Optional Ingress: enable with
> [`values-ingress-example.yaml`](../helm/ovirt-api-simulator/values-ingress-example.yaml)
> (`proxy-intercept-errors: "false"`, `custom-http-errors: "502,503"` so Engine
> fault bodies are not rewritten to branded HTML). See
> [Troubleshooting](troubleshooting.md).

## Prerequisites

- Kubernetes 1.27+ (or comparable)
- Helm 3.14+

## Install

```bash
helm upgrade --install ovirt-sim ./helm/ovirt-api-simulator \
  -n ovirt-sim --create-namespace \
  --set image.repository=inecs/ovirt-api-simulator \
  --set image.tag=0.1.0 \
  --set config.ovirtSeries=4.5 \
  --set seed.profile=minimal \
  --set secrets.ticketSigningKey="$(openssl rand -hex 32)"
```

For a locally built image, set `image.repository` / `image.tag` to match what
you loaded into the cluster.

Render locally:

```bash
make helm-template
```

## Important values

| Value | Purpose |
|---|---|
| `image.repository` / `image.tag` | Container image (default `inecs/ovirt-api-simulator:0.1.0`) |
| `config.ovirtSeries` | Cold-start pack (`4.5`, `3.6`, …) |
| `seed.enabled` / `seed.profile` | Post-install seed Job |
| `postgresql.enabled` | Bundled database |
| `databaseUrl` | External DSN when `postgresql.enabled=false` |
| `secrets.ticketSigningKey` | Rotate on shared clusters |
| `service.port` | Service port (default `8080`) |

See [`values.yaml`](../helm/ovirt-api-simulator/values.yaml).

## Access

Port-forward the simulator Service:

```bash
kubectl -n ovirt-sim port-forward svc/<release>-ovirt-api-simulator 8080:8080
```

Then:

| Surface | URL |
|---|---|
| Engine API | http://127.0.0.1:8080/ovirt-engine/api |
| SSO token | http://127.0.0.1:8080/ovirt-engine/sso/oauth/token |
| Web UI | http://127.0.0.1:8080/ |
| OpenAPI | http://127.0.0.1:8080/docs |

Default seeded login: `admin@internal` / `secret`.

## Manual reseed

```bash
kubectl exec deploy/<release>-ovirt-api-simulator -- \
  python -m app.ovirt.seed_cli --profile demo
```
