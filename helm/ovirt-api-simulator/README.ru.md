**Language / Язык:** [English](README.md) | [Русский](README.ru.md)

# Helm-чарт: ovirt-api-simulator

Ставит Deployment симулятора (порт `8080`), опциональный PostgreSQL,
initContainer migrate и опциональный seed Job.

```bash
helm upgrade --install ovirt-sim . \
  -n ovirt-sim --create-namespace \
  --set image.repository=inecs/ovirt-api-simulator \
  --set image.tag=0.1.0 \
  --set config.ovirtSeries=4.5 \
  --set seed.profile=minimal \
  --set secrets.ticketSigningKey="$(openssl rand -hex 32)"
```

Доступ через port-forward к Service `:8080` (Engine API, SSO, Web UI, `/docs`)
или через Ingress с
[`values-ingress-example.yaml`](values-ingress-example.yaml).

Полное руководство: [docs/ru/kubernetes.md](../../docs/ru/kubernetes.md).  
Values: [`values.yaml`](values.yaml).
