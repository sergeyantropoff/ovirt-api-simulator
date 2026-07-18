**Language / Язык:** [English](python-requests.md) | [Русский](../ru/examples/python-requests.md)

# Python (`requests`)

Minimal pattern against the Engine gateway:

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

Full contract matrix (all clients share the same Engine surface):
`make pulumi-tests` — see [Testing](../testing.md) and
[`pulumi-tests/`](../../pulumi-tests/README.md).
