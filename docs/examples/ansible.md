**Language / Язык:** [English](ansible.md) | [Русский](../ru/examples/ansible.md)

# Ansible

Use `ansible.builtin.uri` against Engine HTTPS:

```yaml
- name: List oVirt VMs
  hosts: local
  gather_facts: false
  vars:
    engine_api: "https://127.0.0.1/ovirt-engine/api"
  tasks:
    - name: GET /vms
      ansible.builtin.uri:
        url: "{{ engine_api }}/vms"
        user: admin@internal
        password: secret
        force_basic_auth: true
        validate_certs: false
        headers:
          Accept: application/json
          Version: "4"
        status_code: [200]
      register: vms
```

Contract coverage for the Engine API: `make pulumi-tests` — see
[Testing](../testing.md) and [`pulumi-tests/`](../../pulumi-tests/README.md).
