**Language / Язык:** [English](../../examples/ansible.md) | [Русский](ansible.md)

# Ansible

Используйте `ansible.builtin.uri` против Engine HTTPS:

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

Нативный suite (150 кейсов): `make test-ansible` / `make test-ansible-smoke` в
[`pulumi-tests/ansible/`](../../../pulumi-tests/README.ru.md).
