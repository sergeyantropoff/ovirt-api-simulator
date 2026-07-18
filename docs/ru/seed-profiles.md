**Language / Язык:** [English](../seed-profiles.md) | [Русский](seed-profiles.md)

# Профили seed

| Профиль | Как загрузить | Содержимое |
|---|---|---|
| `minimal` | Старт (если БД не sized-demo) / `make seed` / `--profile minimal` | 1 DC, 1 cluster, 1 host, Blank, 4 пользователя |
| `small` | `make seed-small` / DATA → **Load small** / `--profile small` | **3 host · 50 ВМ** · 1 DC · 1 cluster · 2 сети · 2 SD |
| `large` | `make seed-large` / DATA → **Load large** / `--profile large` | **10 host · 1000 ВМ** · 2 DC · 2 cluster · пропорциональный инвентарь |
| `big` | `make seed-big` / DATA → **Load big** / `--profile big` | **30 host · 2000 ВМ** · 3 DC · 6 cluster · больше tags/events/jobs |
| `demo` | `make seed-demo` (alias) / `--profile demo` | То же, что **`large`** (старое имя) |

Sized-demo масштабируют DC, clusters, hosts, VMs, сети, storage domains,
templates, tags, events, jobs и nested samples вместе. Lifespan сохраняет
`small` / `large` / `big` / `demo` при рестарте.

Пароль всех пользователей: **`secret`**. Домен: **`internal`**.

## CLI

```bash
make seed
make seed-small
make seed-large   # или: make seed-demo
make seed-big
```

## UI

Ящик **DATA** → **Load small** / **Load large** / **Load big**, либо
**Reset to minimal**.

API: `POST /ui/api/demo/load?size=small|large|big`

## Helm

```yaml
seed:
  enabled: true
  profile: large   # minimal | small | large | big | demo
```
