**Language / Язык:** [English](../seed-profiles.md) | [Русский](seed-profiles.md)

# Профили seed

| Профиль | Как загрузить | Содержимое |
|---|---|---|
| `minimal` | Startup симулятора (если БД ещё не `demo`) / `make seed` / `python -m app.ovirt.seed_cli --profile minimal` / Helm seed Job | 1 datacenter, 1 cluster, 1 host, Blank template, 4 пользователя, небольшой sample инвентаря |
| `demo` | `make seed-demo` / ящик Data в UI / Helm `seed.profile=demo` / `--profile demo` | ~1000 ВМ, multi-host DC, сети, storage domains, диски, nested samples |

В Compose lifespan FastAPI загружает **`minimal`**, если БД пуста или не
помечена как `demo`. Для большого профиля — `make seed-demo` (или ящик Data в
UI). Helm дополнительно может запускать seed Job (`seed.enabled`).

Пароль для всех пользователей: **`secret`**. Домен: **`internal`**.

Principals: `admin@internal`, `ops@internal`, `developer@internal`,
`demo@internal`.

## CLI

```bash
make seed
make seed-demo

# эквивалент
docker compose run --rm --entrypoint python simulator \
  -m app.ovirt.seed_cli --profile demo
```

## Helm

```yaml
seed:
  enabled: true
  profile: demo   # или minimal
```

## Поведение

Оба профиля **очищают** (truncate) лабораторные таблицы oVirt и загружают данные
заново. `demo` — для плотности и nested GET; `minimal` — для быстрого CI.
