"""Large demo datacenter seed (~1000 VMs + full inventory)."""

from __future__ import annotations

import json
from typing import Any

from asyncpg import Connection

from app.ovirt.ids import stable_id
from app.ovirt.seed import DEMO_PROFILE, clear_ovirt_state, seed_ovirt
from app.security.auth import hash_secret

DEMO_VM_COUNT = 1000


async def seed_ovirt_demo(conn: Connection) -> dict[str, Any]:
    """Replace state with a multi-DC demo inventory including ~1000 VMs."""

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

    users = {}
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
    for gname in ("developers", "operators", "readers"):
        await conn.execute(
            "INSERT INTO ov_groups(id, domain_id, name) VALUES($1,$2,$3)",
            stable_id("group", gname),
            domain_id,
            gname,
        )

    # 3 datacenters, multiple clusters/hosts/storage/networks
    dc_specs = [
        ("dc-prod", "Production", False, 4, 5),
        ("dc-stage", "Staging", False, 4, 4),
        ("dc-edge", "Edge", True, 4, 3),
    ]
    clusters: list[tuple[Any, Any, str]] = []
    hosts: list[Any] = []
    networks: list[Any] = []
    profiles: list[Any] = []
    storage_domains: list[Any] = []

    storage_types = ["nfs", "iscsi", "fcp", "localfs"]
    for dc_key, dc_name, local, maj, minor in dc_specs:
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
        for ci in range(2):
            cname = f"{dc_key}-cluster-{ci+1}"
            cid = stable_id("cluster", cname)
            clusters.append((cid, dc_id, cname))
            await conn.execute(
                """INSERT INTO ov_clusters(id, datacenter_id, name, description, version_major, version_minor)
                   VALUES($1,$2,$3,$4,$5,$6)""",
                cid,
                dc_id,
                cname,
                f"Cluster {ci+1} in {dc_name}",
                maj,
                minor,
            )
            await conn.execute(
                """INSERT INTO ov_affinity_groups(id, cluster_id, name, enforcing, positive)
                   VALUES($1,$2,'web-affinity',true,true)""",
                stable_id("ag", cname),
                cid,
            )
            for hi in range(4):
                hname = f"{cname}-host-{hi+1:02d}"
                hid = stable_id("host", hname)
                hosts.append(hid)
                await conn.execute(
                    """INSERT INTO ov_hosts(id, cluster_id, name, address, status, memory, cpu_cores, type)
                       VALUES($1,$2,$3,$4,'up',$5,32,'rhel')""",
                    hid,
                    cid,
                    hname,
                    f"10.{dc_specs.index((dc_key, dc_name, local, maj, minor))+10}.{ci+1}.{hi+10}",
                    (256 + hi * 32) * 1024**3,
                )
        # networks
        for nname, vlan in (("ovirtmgmt", None), ("vm-net", 100), ("storage-net", 200)):
            nid = stable_id("net", dc_key, nname)
            networks.append(nid)
            await conn.execute(
                """INSERT INTO ov_networks(id, datacenter_id, name, description, vlan_id)
                   VALUES($1,$2,$3,$4,$5)""",
                nid,
                dc_id,
                nname if nname != "ovirtmgmt" else f"{dc_key}-ovirtmgmt" if dc_key != "dc-prod" else "ovirtmgmt",
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
        # storage domains
        for si, stype in enumerate(storage_types):
            sname = f"{dc_key}-{stype}-{si+1}"
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
    for tname, mem, cores in (
        ("rhel8-base", 4 * 1024**3, 2),
        ("rhel9-base", 4 * 1024**3, 2),
        ("win2022-base", 8 * 1024**3, 4),
        ("ubuntu2204-base", 2 * 1024**3, 2),
    ):
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

    # ~1000 VMs spread across clusters
    statuses = ["up", "up", "up", "down", "down", "suspended", "powering_up"]
    os_types = ["rhel_8x64", "rhel_9x64", "ubuntu_22_04", "windows_2022", "other"]
    default_profile = profiles[0]
    default_sd = storage_domains[0]

    vm_rows = []
    disk_rows = []
    da_rows = []
    nic_rows = []
    snap_rows = []

    for i in range(DEMO_VM_COUNT):
        cluster_id, _dc, cname = clusters[i % len(clusters)]
        host_id = hosts[i % len(hosts)] if i % 3 != 0 else None
        status = statuses[i % len(statuses)]
        if status == "down":
            host_id = None
        name = f"vm-{i+1:04d}"
        vm_id = stable_id("vm", name)
        memory = (1 + (i % 8)) * 1024**3
        cores = 1 + (i % 8)
        vm_rows.append(
            (
                vm_id,
                cluster_id,
                blank_id,
                name,
                f"Demo VM {i+1}",
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
            snap_rows.append(
                (stable_id("snap", name, "1"), vm_id, f"snapshot-{name}", "ok")
            )

    # Batch insert VMs
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

    # Tags, bookmarks, events, jobs, surface objects
    for tname in ("production", "web", "database", "batch", "gpu"):
        tid = stable_id("tag", tname)
        await conn.execute(
            "INSERT INTO ov_tags(id, name, description) VALUES($1,$2,$3)",
            tid,
            tname,
            f"Tag {tname}",
        )
        for i in range(0, min(50, DEMO_VM_COUNT), 10):
            await conn.execute(
                """INSERT INTO ov_tag_assignments(id, tag_id, object_type, object_id)
                   VALUES($1,$2,'vm',$3) ON CONFLICT DO NOTHING""",
                stable_id("ta", tname, str(i)),
                tid,
                stable_id("vm", f"vm-{i+1:04d}"),
            )

    await conn.execute(
        "INSERT INTO ov_bookmarks(id, name, value) VALUES($1,'UpVMs','Vms: status=up')",
        stable_id("bm", "UpVMs"),
    )
    for i in range(50):
        await conn.execute(
            """INSERT INTO ov_events(code, severity, description, user_id)
               VALUES($1,$2,$3,$4)""",
            1000 + i,
            "normal" if i % 4 else "warning",
            f"Demo event {i}",
            users["admin"],
        )
    for i in range(20):
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

    for collection, names in (
        ("instancetypes", ["Tiny", "Small", "Medium", "Large", "XLarge"]),
        ("macpools", ["Default", "Secondary"]),
        ("schedulingpolicies", ["evenly_distributed", "power_saving", "vm_evenly_distributed"]),
        ("schedulingpolicyunits", ["EvenlyDistributed", "PowerSaving", "VmEvenlyDistributed"]),
        ("clusterlevels", ["4.3", "4.4", "4.5"]),
        ("icons", ["default", "custom"]),
        ("operatingsystems", ["rhel_8x64", "rhel_9x64", "windows_2022", "ubuntu_22_04"]),
        ("networkfilters", ["vdsm-no-mac-spoofing"]),
        ("vmpools", ["web-pool", "batch-pool"]),
        ("affinitylabels", ["label-a", "label-b"]),
        ("katelloerrata", ["RHSA-2024:0001", "RHBA-2024:0002"]),
        ("externalhostproviders", ["foreman-lab"]),
        ("openstacknetworkproviders", ["ovn-provider"]),
        ("openstackimageproviders", ["glance-lab"]),
        ("openstackvolumeproviders", ["cinder-lab"]),
        ("imagetransfers", ["transfer-1"]),
    ):
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
    cluster_ids = [c[0] for c in clusters]
    template_ids = [
        blank_id,
        *[
            stable_id("template", n)
            for n in ("rhel8-base", "rhel9-base", "win2022-base", "ubuntu2204-base")
        ],
    ]
    tag_ids = [stable_id("tag", t) for t in ("production", "web", "database", "batch", "gpu")]
    await seed_nested_for_inventory(
        conn,
        admin_user_id=users["admin"],
        role_user_id=role_user,
        datacenter_ids=dc_ids,
        cluster_ids=cluster_ids,
        host_ids=list(hosts),
        network_ids=list(networks),
        storage_domain_ids=list(storage_domains),
        template_ids=template_ids,
        vm_ids=[stable_id("vm", f"vm-{i:04d}") for i in range(1, DEMO_VM_COUNT + 1)],
        disk_ids=[stable_id("disk", f"vm-{i:04d}") for i in range(1, DEMO_VM_COUNT + 1)],
        tag_ids=tag_ids,
        user_ids=list(users.values()),
        group_ids=[
            stable_id("group", n)
            for n in ("engine-admins", "developers", "operators", "readers")
        ],
    )

    await conn.execute(
        "INSERT INTO ov_demo_meta(key, value) VALUES('profile', $1)", DEMO_PROFILE
    )
    return {
        "profile": DEMO_PROFILE,
        "vms": DEMO_VM_COUNT,
        "hosts": len(hosts),
        "datacenters": len(dc_specs),
        "clusters": len(clusters),
        "storage_domains": len(storage_domains),
        "networks": len(networks),
    }


# Re-export for web routes
__all__ = ["DEMO_PROFILE", "DEMO_VM_COUNT", "clear_ovirt_state", "seed_ovirt", "seed_ovirt_demo"]
