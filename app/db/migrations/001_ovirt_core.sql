-- oVirt Engine identity, inventory, and generic API object store.

CREATE TABLE IF NOT EXISTS ov_domains (
    id uuid PRIMARY KEY,
    name text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS ov_users (
    id uuid PRIMARY KEY,
    domain_id uuid NOT NULL REFERENCES ov_domains(id) ON DELETE CASCADE,
    name text NOT NULL,
    password_hash text NOT NULL,
    enabled boolean NOT NULL DEFAULT true,
    principal text NOT NULL DEFAULT '',
    UNIQUE (domain_id, name)
);

CREATE TABLE IF NOT EXISTS ov_groups (
    id uuid PRIMARY KEY,
    domain_id uuid NOT NULL REFERENCES ov_domains(id) ON DELETE CASCADE,
    name text NOT NULL,
    UNIQUE (domain_id, name)
);

CREATE TABLE IF NOT EXISTS ov_roles (
    id uuid PRIMARY KEY,
    name text NOT NULL UNIQUE,
    description text NOT NULL DEFAULT '',
    administrative boolean NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS ov_permissions (
    id uuid PRIMARY KEY,
    role_id uuid NOT NULL REFERENCES ov_roles(id) ON DELETE CASCADE,
    user_id uuid REFERENCES ov_users(id) ON DELETE CASCADE,
    group_id uuid REFERENCES ov_groups(id) ON DELETE CASCADE,
    object_type text NOT NULL DEFAULT 'system',
    object_id uuid,
    CHECK (user_id IS NOT NULL OR group_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS ov_tokens (
    id text PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES ov_users(id) ON DELETE CASCADE,
    scope text NOT NULL DEFAULT 'ovirt-app-api',
    expires_at timestamptz NOT NULL,
    issued_at timestamptz NOT NULL DEFAULT now(),
    revoked boolean NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS ov_tokens_user_idx ON ov_tokens(user_id);
CREATE INDEX IF NOT EXISTS ov_tokens_expires_idx ON ov_tokens(expires_at);

CREATE TABLE IF NOT EXISTS ov_datacenters (
    id uuid PRIMARY KEY,
    name text NOT NULL UNIQUE,
    description text NOT NULL DEFAULT '',
    local boolean NOT NULL DEFAULT false,
    status text NOT NULL DEFAULT 'up',
    version_major integer NOT NULL DEFAULT 4,
    version_minor integer NOT NULL DEFAULT 5,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ov_clusters (
    id uuid PRIMARY KEY,
    datacenter_id uuid NOT NULL REFERENCES ov_datacenters(id) ON DELETE CASCADE,
    name text NOT NULL,
    description text NOT NULL DEFAULT '',
    cpu_type text NOT NULL DEFAULT 'Intel Conroe Family',
    version_major integer NOT NULL DEFAULT 4,
    version_minor integer NOT NULL DEFAULT 5,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (datacenter_id, name)
);

CREATE TABLE IF NOT EXISTS ov_hosts (
    id uuid PRIMARY KEY,
    cluster_id uuid NOT NULL REFERENCES ov_clusters(id) ON DELETE CASCADE,
    name text NOT NULL UNIQUE,
    address text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'up',
    type text NOT NULL DEFAULT 'rhel',
    memory bigint NOT NULL DEFAULT 0,
    cpu_cores integer NOT NULL DEFAULT 8,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ov_networks (
    id uuid PRIMARY KEY,
    datacenter_id uuid NOT NULL REFERENCES ov_datacenters(id) ON DELETE CASCADE,
    name text NOT NULL,
    description text NOT NULL DEFAULT '',
    vlan_id integer,
    stp boolean NOT NULL DEFAULT false,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (datacenter_id, name)
);

CREATE TABLE IF NOT EXISTS ov_vnic_profiles (
    id uuid PRIMARY KEY,
    network_id uuid NOT NULL REFERENCES ov_networks(id) ON DELETE CASCADE,
    name text NOT NULL,
    pass_through boolean NOT NULL DEFAULT false,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (network_id, name)
);

CREATE TABLE IF NOT EXISTS ov_storage_domains (
    id uuid PRIMARY KEY,
    name text NOT NULL UNIQUE,
    type text NOT NULL DEFAULT 'data',
    storage_type text NOT NULL DEFAULT 'nfs',
    status text NOT NULL DEFAULT 'active',
    available bigint NOT NULL DEFAULT 0,
    used bigint NOT NULL DEFAULT 0,
    committed bigint NOT NULL DEFAULT 0,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ov_storage_domain_attachments (
    id uuid PRIMARY KEY,
    storage_domain_id uuid NOT NULL REFERENCES ov_storage_domains(id) ON DELETE CASCADE,
    datacenter_id uuid NOT NULL REFERENCES ov_datacenters(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'active',
    UNIQUE (storage_domain_id, datacenter_id)
);

CREATE TABLE IF NOT EXISTS ov_storage_connections (
    id uuid PRIMARY KEY,
    type text NOT NULL DEFAULT 'nfs',
    address text NOT NULL DEFAULT '',
    path text NOT NULL DEFAULT '',
    data jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS ov_templates (
    id uuid PRIMARY KEY,
    cluster_id uuid REFERENCES ov_clusters(id) ON DELETE SET NULL,
    name text NOT NULL UNIQUE,
    description text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'ok',
    memory bigint NOT NULL DEFAULT 1073741824,
    cpu_sockets integer NOT NULL DEFAULT 1,
    cpu_cores integer NOT NULL DEFAULT 1,
    data jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS ov_vms (
    id uuid PRIMARY KEY,
    cluster_id uuid NOT NULL REFERENCES ov_clusters(id) ON DELETE CASCADE,
    template_id uuid REFERENCES ov_templates(id) ON DELETE SET NULL,
    name text NOT NULL,
    description text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'down',
    memory bigint NOT NULL DEFAULT 1073741824,
    cpu_sockets integer NOT NULL DEFAULT 1,
    cpu_cores integer NOT NULL DEFAULT 1,
    cpu_threads integer NOT NULL DEFAULT 1,
    os_type text NOT NULL DEFAULT 'other',
    type text NOT NULL DEFAULT 'server',
    host_id uuid REFERENCES ov_hosts(id) ON DELETE SET NULL,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (cluster_id, name)
);
CREATE INDEX IF NOT EXISTS ov_vms_status_idx ON ov_vms(status);
CREATE INDEX IF NOT EXISTS ov_vms_name_idx ON ov_vms(name);

CREATE TABLE IF NOT EXISTS ov_disks (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    description text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'ok',
    provisioned_size bigint NOT NULL DEFAULT 0,
    actual_size bigint NOT NULL DEFAULT 0,
    format text NOT NULL DEFAULT 'cow',
    sparse boolean NOT NULL DEFAULT true,
    shareable boolean NOT NULL DEFAULT false,
    wipe_after_delete boolean NOT NULL DEFAULT false,
    storage_domain_id uuid REFERENCES ov_storage_domains(id) ON DELETE SET NULL,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ov_disk_attachments (
    id uuid PRIMARY KEY,
    vm_id uuid NOT NULL REFERENCES ov_vms(id) ON DELETE CASCADE,
    disk_id uuid NOT NULL REFERENCES ov_disks(id) ON DELETE CASCADE,
    active boolean NOT NULL DEFAULT true,
    bootable boolean NOT NULL DEFAULT false,
    interface text NOT NULL DEFAULT 'virtio_scsi',
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (vm_id, disk_id)
);

CREATE TABLE IF NOT EXISTS ov_nics (
    id uuid PRIMARY KEY,
    vm_id uuid NOT NULL REFERENCES ov_vms(id) ON DELETE CASCADE,
    name text NOT NULL,
    interface text NOT NULL DEFAULT 'virtio',
    linked boolean NOT NULL DEFAULT true,
    plugged boolean NOT NULL DEFAULT true,
    mac_address text NOT NULL DEFAULT '',
    vnic_profile_id uuid REFERENCES ov_vnic_profiles(id) ON DELETE SET NULL,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (vm_id, name)
);

CREATE TABLE IF NOT EXISTS ov_snapshots (
    id uuid PRIMARY KEY,
    vm_id uuid NOT NULL REFERENCES ov_vms(id) ON DELETE CASCADE,
    description text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'ok',
    snapshot_type text NOT NULL DEFAULT 'user',
    persist_memorystate boolean NOT NULL DEFAULT false,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ov_tags (
    id uuid PRIMARY KEY,
    name text NOT NULL UNIQUE,
    description text NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS ov_tag_assignments (
    id uuid PRIMARY KEY,
    tag_id uuid NOT NULL REFERENCES ov_tags(id) ON DELETE CASCADE,
    object_type text NOT NULL,
    object_id uuid NOT NULL,
    UNIQUE (tag_id, object_type, object_id)
);

CREATE TABLE IF NOT EXISTS ov_affinity_groups (
    id uuid PRIMARY KEY,
    cluster_id uuid NOT NULL REFERENCES ov_clusters(id) ON DELETE CASCADE,
    name text NOT NULL,
    description text NOT NULL DEFAULT '',
    enforcing boolean NOT NULL DEFAULT true,
    positive boolean NOT NULL DEFAULT true,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (cluster_id, name)
);

CREATE TABLE IF NOT EXISTS ov_quotas (
    id uuid PRIMARY KEY,
    datacenter_id uuid NOT NULL REFERENCES ov_datacenters(id) ON DELETE CASCADE,
    name text NOT NULL,
    description text NOT NULL DEFAULT '',
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (datacenter_id, name)
);

CREATE TABLE IF NOT EXISTS ov_bookmarks (
    id uuid PRIMARY KEY,
    name text NOT NULL UNIQUE,
    value text NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS ov_events (
    id bigserial PRIMARY KEY,
    code integer NOT NULL DEFAULT 0,
    severity text NOT NULL DEFAULT 'normal',
    description text NOT NULL DEFAULT '',
    time timestamptz NOT NULL DEFAULT now(),
    user_id uuid REFERENCES ov_users(id) ON DELETE SET NULL,
    vm_id uuid REFERENCES ov_vms(id) ON DELETE SET NULL,
    host_id uuid REFERENCES ov_hosts(id) ON DELETE SET NULL,
    data jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS ov_jobs (
    id uuid PRIMARY KEY,
    description text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'started',
    auto_cleared boolean NOT NULL DEFAULT true,
    started timestamptz NOT NULL DEFAULT now(),
    ended timestamptz,
    owner_id uuid REFERENCES ov_users(id) ON DELETE SET NULL,
    data jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS ov_job_steps (
    id uuid PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES ov_jobs(id) ON DELETE CASCADE,
    description text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'started',
    type text NOT NULL DEFAULT 'validating',
    number integer NOT NULL DEFAULT 1,
    started timestamptz NOT NULL DEFAULT now(),
    ended timestamptz,
    data jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- Generic store for surface-complete collections not given dedicated tables.
CREATE TABLE IF NOT EXISTS ov_api_objects (
    id uuid PRIMARY KEY,
    collection text NOT NULL,
    name text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'ok',
    parent_collection text,
    parent_id uuid,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ov_api_objects_collection_idx ON ov_api_objects(collection);
CREATE INDEX IF NOT EXISTS ov_api_objects_parent_idx ON ov_api_objects(parent_collection, parent_id);

CREATE TABLE IF NOT EXISTS ov_demo_meta (
    key text PRIMARY KEY,
    value text NOT NULL
);

CREATE TABLE IF NOT EXISTS ov_runtime_meta (
    key text PRIMARY KEY,
    value text NOT NULL
);
