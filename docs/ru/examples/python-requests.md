**Language / Язык:** [English](../../examples/python-requests.md) | [Русский](python-requests.md)

# Python (`requests`)

Минимальный паттерн против Engine gateway:

```python
import requests

BASE = "https://127.0.0.1/ovirt-engine/api"
AUTH = ("admin@internal", "secret")
HEADERS = {"Accept": "application/json", "Version": "4"}

r = requests.get(f"{BASE}/vms", auth=AUTH, headers=HEADERS, verify=False, timeout=60)
r.raise_for_status()
print(r.json())
```

OAuth password grant:

```python
token = requests.post(
    "https://127.0.0.1/ovirt-engine/sso/oauth/token",
    data={
        "grant_type": "password",
        "username": "admin@internal",
        "password": "secret",
        "scope": "ovirt-app-api",
    },
    verify=False,
    timeout=60,
).json()["access_token"]

r = requests.get(
    f"{BASE}/vms",
    headers={**HEADERS, "Authorization": f"Bearer {token}"},
    verify=False,
    timeout=60,
)
```

Полная матрица контрактов (общий Engine surface для всех клиентов):
`make pulumi-tests` — см. [Тестирование](../testing.md) и
[`pulumi-tests/`](../../../pulumi-tests/README.ru.md).
