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

Native suite (150 cases): `make test-ansible` / `make test-ansible-smoke` under
[`pulumi-tests/ansible/`](../../pulumi-tests/README.md).
