"""Sized cluster demo seeds: small / large / big (+ demo→large alias)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from asyncpg import Connection

from app.ovirt.ids import stable_id
from app.ovirt.seed import clear_ovirt_state
from app.security.auth import hash_secret


@dataclass(frozen=True)
class ClusterSizeSpec:
    """Topology + inventory density for a demo cluster size."""

    name: str
    hosts: int
    vms: int
    datacenters: int
    clusters_per_dc: int
    hosts_per_cluster: int
    networks_per_dc: int
    storage_per_dc: int
    templates: tuple[str, ...]
    tags: tuple[str, ...]
    groups: tuple[str, ...]
    events: int
    jobs: int
    bookmarks: tuple[tuple[str, str], ...]
    instancetypes: tuple[str, ...]
    macpools: tuple[str, ...]
    vmpools: tuple[str, ...]
    affinitylabels: tuple[str, ...]
    katelloerrata: tuple[str, ...]
    icons: tuple[str, ...]
    operatingsystems: tuple[str, ...]


CLUSTER_SIZES: dict[str, ClusterSizeSpec] = {
    "small": ClusterSizeSpec(
        name="small",
        hosts=3,
        vms=50,
        datacenters=1,
        clusters_per_dc=1,
        hosts_per_cluster=3,
        networks_per_dc=2,
        storage_per_dc=2,
        templates=("rhel9-base", "ubuntu2204-base"),
        tags=("lab", "web"),
        groups=("developers", "readers"),
        events=15,
        jobs=5,
        bookmarks=(("UpVMs", "Vms: status=up"),),
        instancetypes=("Small", "Medium"),
        macpools=("Default",),
        vmpools=("web-pool",),
        affinitylabels=("label-a",),
        katelloerrata=("RHSA-2024:0001",),
        icons=("default",),
        operatingsystems=("rhel_9x64", "ubuntu_22_04"),
    ),
    "large": ClusterSizeSpec(
        name="large",
        hosts=10,
        vms=1000,
        datacenters=2,
        clusters_per_dc=1,
        hosts_per_cluster=5,
        networks_per_dc=3,
        storage_per_dc=3,
        templates=("rhel8-base", "rhel9-base", "win2022-base", "ubuntu2204-base"),
        tags=("production", "web", "database", "batch", "gpu"),
        groups=("developers", "operators", "readers"),
        events=50,
        jobs=20,
        bookmarks=(
            ("UpVMs", "Vms: status=up"),
            ("DownVMs", "Vms: status=down"),
        ),
        instancetypes=("Tiny", "Small", "Medium", "Large", "XLarge"),
        macpools=("Default", "Secondary"),
        vmpools=("web-pool", "batch-pool"),
        affinitylabels=("label-a", "label-b"),
        katelloerrata=("RHSA-2024:0001", "RHBA-2024:0002"),
        icons=("default", "custom"),
        operatingsystems=("rhel_8x64", "rhel_9x64", "windows_2022", "ubuntu_22_04"),
    ),
    "big": ClusterSizeSpec(
        name="big",
        hosts=30,
        vms=2000,
        datacenters=3,
        clusters_per_dc=2,
        hosts_per_cluster=5,
        networks_per_dc=3,
        storage_per_dc=4,
        templates=(
            "rhel8-base",
            "rhel9-base",
            "win2022-base",
            "ubuntu2204-base",
            "centos-stream9",
            "debian12-base",
        ),
        tags=(
            "production",
            "web",
            "database",
            "batch",
            "gpu",
            "edge",
            "staging",
            "critical",
        ),
        groups=("developers", "operators", "readers", "auditors"),
        events=120,
        jobs=40,
        bookmarks=(
            ("UpVMs", "Vms: status=up"),
            ("DownVMs", "Vms: status=down"),
            ("ProdHosts", "Hosts:"),
        ),
        instancetypes=("Tiny", "Small", "Medium", "Large", "XLarge", "2XLarge", "4XLarge"),
        macpools=("Default", "Secondary", "Edge"),
        vmpools=("web-pool", "batch-pool", "gpu-pool", "edge-pool"),
        affinitylabels=("label-a", "label-b", "label-c", "label-d"),
        katelloerrata=("RHSA-2024:0001", "RHBA-2024:0002", "RHSA-2024:1001"),
        icons=("default", "custom", "windows", "linux"),
        operatingsystems=(
            "rhel_8x64",
            "rhel_9x64",
            "windows_2022",
            "ubuntu_22_04",
            "centos_stream9",
            "debian_12",
        ),
    ),
}

# Canonical demo profile names that must not be wiped on simulator restart.
DEMO_PROFILES: frozenset[str] = frozenset(CLUSTER_SIZES) | {"demo"}
# Default / legacy alias target.
DEMO_PROFILE = "large"
DEMO_VM_COUNT = CLUSTER_SIZES["large"].vms


def normalize_cluster_size(size: str | None) -> str:
    """Map CLI/UI aliases to a ClusterSizeSpec name."""

    key = (size or DEMO_PROFILE).strip().lower()
    if key == "demo":
        return "large"
    if key not in CLUSTER_SIZES:
        raise ValueError(f"unknown cluster size {size!r}; expected small|large|big|demo")
    return key


def cluster_size_spec(size: str | None = None) -> ClusterSizeSpec:
    return CLUSTER_SIZES[normalize_cluster_size(size)]


_DC_NAMES = (
    ("dc-prod", "Production", False, 4, 5),
    ("dc-stage", "Staging", False, 4, 4),
    ("dc-edge", "Edge", True, 4, 3),
)
_NETWORK_SPECS = (("ovirtmgmt", None), ("vm-net", 100), ("storage-net", 200))
_STORAGE_TYPES = ("nfs", "iscsi", "fcp", "localfs")
_TEMPLATE_SPECS: dict[str, tuple[int, int]] = {
    "rhel8-base": (4 * 1024**3, 2),
    "rhel9-base": (4 * 1024**3, 2),
    "win2022-base": (8 * 1024**3, 4),
    "ubuntu2204-base": (2 * 1024**3, 2),
    "centos-stream9": (4 * 1024**3, 2),
    "debian12-base": (2 * 1024**3, 2),
}


async def seed_ovirt_demo(conn: Connection, size: str | None = None) -> dict[str, Any]:
    """Replace state with a sized multi-host demo inventory."""

    spec = cluster_size_spec(size)
    expected_hosts = spec.datacenters * spec.clusters_per_dc * spec.hosts_per_cluster
    if expected_hosts != spec.hosts:
        raise RuntimeError(
            f"cluster size {spec.name}: topology hosts {expected_hosts} != declared {spec.hosts}"
        )

    await clear_ovirt_state(conn)

    domain_id = stable_id("domain", "internal")
    await conn.execute("INSERT INTO ov_domains(id, name) VALUES($1,'internal')", domain_id)
    pwd = hash_secret("secret", salt=b"ovirt-sim-v1-salt!")
    role_super = stable_id("role", "SuperUser")
    role_user = stable_id("role", "UserRole")
    role_cluster = stable_id("role", "ClusterAdmin")
    for rid, name, admin in (
        (role_super, "SuperUser", True),
        (role_user, "UserRole", False),
        (role_cluster, "ClusterAdmin", True),
        (stable_id("role", "TemplateAdmin"), "TemplateAdmin", True),
        (stable_id("role", "StorageAdmin"), "StorageAdmin", True),
    ):
        await conn.execute(
            "INSERT INTO ov_roles(id, name, administrative) VALUES($1,$2,$3)",
            rid,
            name,
            admin,
        )

    users: dict[str, Any] = {}
    for uname, role in (
        ("admin", role_super),
        ("ops", role_cluster),
        ("developer", role_user),
        ("demo", role_user),
    ):
        uid = stable_id("user", uname)
        users[uname] = uid
        await conn.execute(
            """INSERT INTO ov_users(id, domain_id, name, password_hash, enabled, principal)
               VALUES($1,$2,$3,$4,true,$5)""",
            uid,
            domain_id,
            uname,
            pwd,
            f"{uname}@internal",
        )
        await conn.execute(
            """INSERT INTO ov_permissions(id, role_id, user_id, object_type)
               VALUES($1,$2,$3,'system')""",
            stable_id("perm", uname),
            role,
            uid,
        )

    await conn.execute(
        "INSERT INTO ov_groups(id, domain_id, name) VALUES($1,$2,'engine-admins')",
        stable_id("group", "engine-admins"),
        domain_id,
    )
    for gname in spec.groups:
        await conn.execute(
            "INSERT INTO ov_groups(id, domain_id, name) VALUES($1,$2,$3)",
            stable_id("group", gname),
            domain_id,
            gname,
        )

    dc_specs = list(_DC_NAMES[: spec.datacenters])
    clusters: list[tuple[Any, Any, str]] = []
    hosts: list[Any] = []
    networks: list[Any] = []
    profiles: list[Any] = []
    storage_domains: list[Any] = []

    for dc_idx, (dc_key, dc_name, local, maj, minor) in enumerate(dc_specs):
        dc_id = stable_id("dc", dc_key)
        await conn.execute(
            """INSERT INTO ov_datacenters(id, name, description, local, status, version_major, version_minor)
               VALUES($1,$2,$3,$4,'up',$5,$6)""",
            dc_id,
            dc_name,
            f"{dc_name} datacenter",
            local,
            maj,
            minor,
        )
        await conn.execute(
            """INSERT INTO ov_quotas(id, datacenter_id, name, description)
               VALUES($1,$2,'Default','Default quota')""",
            stable_id("quota", dc_key),
            dc_id,
        )
        for ci in range(spec.clusters_per_dc):
            cname = f"{dc_key}-cluster-{ci + 1}"
            cid = stable_id("cluster", cname)
            clusters.append((cid, dc_id, cname))
            await conn.execute(
                """INSERT INTO ov_clusters(id, datacenter_id, name, description, version_major, version_minor)
                   VALUES($1,$2,$3,$4,$5,$6)""",
                cid,
                dc_id,
                cname,
                f"Cluster {ci + 1} in {dc_name}",
                maj,
                minor,
            )
            await conn.execute(
                """INSERT INTO ov_affinity_groups(id, cluster_id, name, enforcing, positive)
                   VALUES($1,$2,'web-affinity',true,true)""",
                stable_id("ag", cname),
                cid,
            )
            for hi in range(spec.hosts_per_cluster):
                hname = f"{cname}-host-{hi + 1:02d}"
                hid = stable_id("host", hname)
                hosts.append(hid)
                await conn.execute(
                    """INSERT INTO ov_hosts(id, cluster_id, name, address, status, memory, cpu_cores, type)
                       VALUES($1,$2,$3,$4,'up',$5,32,'rhel')""",
                    hid,
                    cid,
                    hname,
                    f"10.{10 + dc_idx}.{ci + 1}.{hi + 10}",
                    (256 + hi * 32) * 1024**3,
                )

        for nname, vlan in _NETWORK_SPECS[: spec.networks_per_dc]:
            nid = stable_id("net", dc_key, nname)
            networks.append(nid)
            if nname == "ovirtmgmt" and dc_key == "dc-prod":
                net_label = "ovirtmgmt"
            elif nname == "ovirtmgmt":
                net_label = f"{dc_key}-ovirtmgmt"
            elif spec.datacenters > 1:
                net_label = f"{dc_key}-{nname}"
            else:
                net_label = nname
            await conn.execute(
                """INSERT INTO ov_networks(id, datacenter_id, name, description, vlan_id)
                   VALUES($1,$2,$3,$4,$5)""",
                nid,
                dc_id,
                net_label,
                f"{nname} in {dc_name}",
                vlan,
            )
            pid = stable_id("vnic", dc_key, nname)
            profiles.append(pid)
            await conn.execute(
                "INSERT INTO ov_vnic_profiles(id, network_id, name) VALUES($1,$2,$3)",
                pid,
                nid,
                nname,
            )

        for si, stype in enumerate(_STORAGE_TYPES[: spec.storage_per_dc]):
            sname = f"{dc_key}-{stype}-{si + 1}"
            sid = stable_id("sd", sname)
            storage_domains.append(sid)
            await conn.execute(
                """INSERT INTO ov_storage_domains(id, name, type, storage_type, status, available, used)
                   VALUES($1,$2,'data',$3,'active',$4,$5)""",
                sid,
                sname,
                stype,
                (5 + si) * 1024**4,
                si * 200 * 1024**3,
            )
            await conn.execute(
                """INSERT INTO ov_storage_domain_attachments(id, storage_domain_id, datacenter_id, status)
                   VALUES($1,$2,$3,'active')""",
                stable_id("sda", sname),
                sid,
                dc_id,
            )
            await conn.execute(
                """INSERT INTO ov_storage_connections(id, type, address, path)
                   VALUES($1,$2,$3,$4)""",
                stable_id("sc", sname),
                stype if stype != "localfs" else "localfs",
                f"storage-{si}.lab.local",
                f"/export/{sname}",
            )

    blank_id = stable_id("template", "Blank")
    await conn.execute(
        """INSERT INTO ov_templates(id, cluster_id, name, description, status, memory, cpu_sockets, cpu_cores)
           VALUES($1,$2,'Blank','Blank template','ok',$3,1,1)""",
        blank_id,
        clusters[0][0],
        1024**3,
    )
    for tname in spec.templates:
        mem, cores = _TEMPLATE_SPECS.get(tname, (2 * 1024**3, 2))
        await conn.execute(
            """INSERT INTO ov_templates(id, cluster_id, name, description, status, memory, cpu_sockets, cpu_cores)
               VALUES($1,$2,$3,$4,'ok',$5,1,$6)""",
            stable_id("template", tname),
            clusters[0][0],
            tname,
            f"Template {tname}",
            mem,
            cores,
        )

    statuses = ["up", "up", "up", "down", "down", "suspended", "powering_up"]
    os_types = list(spec.operatingsystems) or ["other"]
    default_profile = profiles[0]

    vm_rows = []
    disk_rows = []
    da_rows = []
    nic_rows = []
    snap_rows = []

    for i in range(spec.vms):
        cluster_id, _dc, _cname = clusters[i % len(clusters)]
        host_id = hosts[i % len(hosts)] if i % 3 != 0 else None
        status = statuses[i % len(statuses)]
        if status == "down":
            host_id = None
        name = f"vm-{i + 1:04d}"
        vm_id = stable_id("vm", name)
        memory = (1 + (i % 8)) * 1024**3
        cores = 1 + (i % 8)
        vm_rows.append(
            (
                vm_id,
                cluster_id,
                blank_id,
                name,
                f"Demo VM {i + 1}",
                status,
                memory,
                1,
                cores,
                1,
                os_types[i % len(os_types)],
                "server" if i % 5 else "desktop",
                host_id,
            )
        )
        disk_id = stable_id("disk", name)
        size = (10 + (i % 50)) * 1024**3
        disk_rows.append(
            (disk_id, f"{name}_Disk1", size, size, storage_domains[i % len(storage_domains)])
        )
        da_rows.append((stable_id("da", name), vm_id, disk_id, True))
        nic_rows.append(
            (
                stable_id("nic", name),
                vm_id,
                "nic1",
                f"00:1a:4a:{(i >> 16) & 0xFF:02x}:{(i >> 8) & 0xFF:02x}:{i & 0xFF:02x}",
                profiles[i % len(profiles)] if profiles else default_profile,
            )
        )
        if i % 7 == 0:
            snap_rows.append((stable_id("snap", name, "1"), vm_id, f"snapshot-{name}", "ok"))

    await conn.executemany(
        """INSERT INTO ov_vms(id, cluster_id, template_id, name, description, status,
           memory, cpu_sockets, cpu_cores, cpu_threads, os_type, type, host_id)
           VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)""",
        vm_rows,
    )
    await conn.executemany(
        """INSERT INTO ov_disks(id, name, provisioned_size, actual_size, storage_domain_id)
           VALUES($1,$2,$3,$4,$5)""",
        disk_rows,
    )
    await conn.executemany(
        """INSERT INTO ov_disk_attachments(id, vm_id, disk_id, bootable)
           VALUES($1,$2,$3,$4)""",
        da_rows,
    )
    await conn.executemany(
        """INSERT INTO ov_nics(id, vm_id, name, mac_address, vnic_profile_id)
           VALUES($1,$2,$3,$4,$5)""",
        nic_rows,
    )
    if snap_rows:
        await conn.executemany(
            """INSERT INTO ov_snapshots(id, vm_id, description, status)
               VALUES($1,$2,$3,$4)""",
            snap_rows,
        )

    tag_step = max(1, spec.vms // 10)
    for tname in spec.tags:
        tid = stable_id("tag", tname)
        await conn.execute(
            "INSERT INTO ov_tags(id, name, description) VALUES($1,$2,$3)",
            tid,
            tname,
            f"Tag {tname}",
        )
        for i in range(0, min(spec.vms, tag_step * 5), tag_step):
            await conn.execute(
                """INSERT INTO ov_tag_assignments(id, tag_id, object_type, object_id)
                   VALUES($1,$2,'vm',$3) ON CONFLICT DO NOTHING""",
                stable_id("ta", tname, str(i)),
                tid,
                stable_id("vm", f"vm-{i + 1:04d}"),
            )

    for bname, bvalue in spec.bookmarks:
        await conn.execute(
            "INSERT INTO ov_bookmarks(id, name, value) VALUES($1,$2,$3)",
            stable_id("bm", bname),
            bname,
            bvalue,
        )
    for i in range(spec.events):
        await conn.execute(
            """INSERT INTO ov_events(code, severity, description, user_id)
               VALUES($1,$2,$3,$4)""",
            1000 + i,
            "normal" if i % 4 else "warning",
            f"Demo event {i}",
            users["admin"],
        )
    for i in range(spec.jobs):
        jid = stable_id("job", str(i))
        await conn.execute(
            """INSERT INTO ov_jobs(id, description, status, owner_id)
               VALUES($1,$2,'finished',$3)""",
            jid,
            f"Demo job {i}",
            users["admin"],
        )
        await conn.execute(
            """INSERT INTO ov_job_steps(id, job_id, description, status, type, number)
               VALUES($1,$2,$3,'finished','executing',1)""",
            stable_id("step", str(i)),
            jid,
            f"Step for job {i}",
        )

    surface: list[tuple[str, tuple[str, ...]]] = [
        ("instancetypes", spec.instancetypes),
        ("macpools", spec.macpools),
        (
            "schedulingpolicies",
            ("evenly_distributed", "power_saving", "vm_evenly_distributed"),
        ),
        (
            "schedulingpolicyunits",
            ("EvenlyDistributed", "PowerSaving", "VmEvenlyDistributed"),
        ),
        ("clusterlevels", ("4.3", "4.4", "4.5")),
        ("icons", spec.icons),
        ("operatingsystems", spec.operatingsystems),
        ("networkfilters", ("vdsm-no-mac-spoofing",)),
        ("vmpools", spec.vmpools),
        ("affinitylabels", spec.affinitylabels),
        ("katelloerrata", spec.katelloerrata),
        ("externalhostproviders", ("foreman-lab",)),
        ("openstacknetworkproviders", ("ovn-provider",)),
        ("openstackimageproviders", ("glance-lab",)),
        ("openstackvolumeproviders", ("cinder-lab",)),
        ("imagetransfers", ("transfer-1",)),
    ]
    for collection, names in surface:
        for name in names:
            await conn.execute(
                """INSERT INTO ov_api_objects(id, collection, name, status, data)
                   VALUES($1,$2,$3,'ok',$4::jsonb)""",
                stable_id("obj", collection, name),
                collection,
                name,
                json.dumps({"name": name, "description": f"demo {collection}"}),
            )

    from app.ovirt.settings import seed_engine_options

    await seed_engine_options(conn)

    from app.ovirt.seed_nested import seed_nested_for_inventory

    dc_ids = [stable_id("dc", key) for key, *_ in dc_specs]
    template_ids = [blank_id, *[stable_id("template", n) for n in spec.templates]]
    tag_ids = [stable_id("tag", t) for t in spec.tags]
    await seed_nested_for_inventory(
        conn,
        admin_user_id=users["admin"],
        role_user_id=role_user,
        datacenter_ids=dc_ids,
        cluster_ids=[c[0] for c in clusters],
        host_ids=list(hosts),
        network_ids=list(networks),
        storage_domain_ids=list(storage_domains),
        template_ids=template_ids,
        vm_ids=[stable_id("vm", f"vm-{i:04d}") for i in range(1, spec.vms + 1)],
        disk_ids=[stable_id("disk", f"vm-{i:04d}") for i in range(1, spec.vms + 1)],
        tag_ids=tag_ids,
        user_ids=list(users.values()),
        group_ids=[
            stable_id("group", n)
            for n in ("engine-admins", *spec.groups)
        ],
    )

    await conn.execute(
        "INSERT INTO ov_demo_meta(key, value) VALUES('profile', $1)", spec.name
    )
    return {
        "profile": spec.name,
        "vms": spec.vms,
        "hosts": len(hosts),
        "datacenters": len(dc_specs),
        "clusters": len(clusters),
        "storage_domains": len(storage_domains),
        "networks": len(networks),
    }


__all__ = [
    "CLUSTER_SIZES",
    "DEMO_PROFILE",
    "DEMO_PROFILES",
    "DEMO_VM_COUNT",
    "clear_ovirt_state",
    "cluster_size_spec",
    "normalize_cluster_size",
    "seed_ovirt_demo",
]
