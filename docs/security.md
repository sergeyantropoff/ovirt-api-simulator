**Language / Язык:** [English](security.md) | [Русский](ru/security.md)

# Security

This project is a **laboratory simulator**, not a hardened Engine deployment.

## Credentials

Default seeded password is `secret` for all lab users. Treat Compose TLS
certificates under `docker/tls/` as **dev-only**.

## Signing key

`TICKET_SIGNING_KEY` / Helm `secrets.ticketSigningKey` must be rotated on any
shared or long-lived cluster. The `.env.example` value is intentionally weak.

## Network exposure

Only publish Engine + UI ports to trusted networks. Do not expose the simulator
to the public Internet without additional controls.

## TLS

Compose gateway presents a local self-signed certificate on
`OVIRT_ENGINE_PORT`. Use `curl -k` / client `insecure` flags in labs, or replace
the certs under `docker/tls/`.

## Threat model (lab)

| In scope | Out of scope |
|---|---|
| Auth shape (Basic / OAuth) for client testing | Real AAA / AD / IPA integration |
| Isolating toy credentials in docs | Production secret management |
| Avoiding accidental public bind | Full Engine hardening checklist |
