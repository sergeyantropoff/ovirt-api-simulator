**Language / Язык:** [English](README.md) | [Русский](README.ru.md)

# Helm chart: ovirt-api-simulator

Installs the simulator Deployment (port `8080`), optional bundled PostgreSQL,
migrate initContainer, and optional seed Job.

```bash
helm upgrade --install ovirt-sim . \
  -n ovirt-sim --create-namespace \
  --set image.repository=inecs/ovirt-api-simulator \
  --set image.tag=0.1.0 \
  --set config.ovirtSeries=4.5 \
  --set seed.profile=minimal \
  --set secrets.ticketSigningKey="$(openssl rand -hex 32)"
```

Access via port-forward to Service `:8080` (Engine API, SSO, Web UI, `/docs`).
The Compose nginx gateway is **not** part of this chart yet.

Full guide: [docs/kubernetes.md](../../docs/kubernetes.md).  
Values: [`values.yaml`](values.yaml).
