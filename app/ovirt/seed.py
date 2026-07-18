"""Minimal and demo seed profiles for the oVirt Engine simulator."""

from __future__ import annotations

import json
from typing import Any

from asyncpg import Connection

from app.ovirt.ids import stable_id
from app.security.auth import hash_secret

MINIMAL_PROFILE = "minimal"
# Legacy name kept for imports; sized demos live in demo_datacenter.DEMO_PROFILES.
DEMO_PROFILE = "large"


async def clear_ovirt_state(conn: Connection) -> None:
    tables = [
        "ov_job_steps",
        "ov_jobs",
        "ov_events",
        "ov_tag_assignments",
        "ov_tags",
        "ov_snapshots",
        "ov_nics",
        "ov_disk_attachments",
        "ov_disks",
        "ov_vms",
        "ov_templates",
        "ov_affinity_groups",
        "ov_quotas",
        "ov_vnic_profiles",
        "ov_networks",
        "ov_storage_domain_attachments",
        "ov_storage_domains",
        "ov_storage_connections",
        "ov_hosts",
        "ov_clusters",
        "ov_datacenters",
        "ov_bookmarks",
        "ov_permissions",
        "ov_tokens",
        "ov_users",
        "ov_groups",
        "ov_roles",
        "ov_domains",
        "ov_api_objects",
        "ov_demo_meta",
    ]
    for table in tables:
        await conn.execute(f"TRUNCATE TABLE {table} CASCADE")


async def seed_ovirt(conn: Connection) -> dict[str, Any]:
    """Minimal lab: 1 DC, 1 cluster, 1 host, Blank template, admin user."""

    await clear_ovirt_state(conn)
    domain_id = stable_id("domain", "internal")
    await conn.execute(
        "INSERT INTO ov_domains(id, name) VALUES($1, 'internal')", domain_id
    )
    roles = [
        (stable_id("role", "SuperUser"), "SuperUser", True),
        (stable_id("role", "UserRole"), "UserRole", False),
        (stable_id("role", "ClusterAdmin"), "ClusterAdmin", True),
    ]
    for rid, name, admin in roles:
        await conn.execute(
            "INSERT INTO ov_roles(id, name, administrative) VALUES($1,$2,$3)",
            rid,
            name,
            admin,
        )
    admin_id = stable_id("user", "admin")
    pwd = hash_secret("secret", salt=b"ovirt-sim-v1-salt!")
    await conn.execute(
        """INSERT INTO ov_users(id, domain_id, name, password_hash, enabled, principal)
           VALUES($1,$2,'admin',$3,true,'admin@internal')""",
        admin_id,
        domain_id,
        pwd,
    )
    await conn.execute(
        """INSERT INTO ov_permissions(id, role_id, user_id, object_type)
           VALUES($1,$2,$3,'system')""",
        stable_id("perm", "admin-super"),
        roles[0][0],
        admin_id,
    )
    # Extra lab users
    for uname in ("ops", "developer", "demo"):
        uid = stable_id("user", uname)
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
            roles[1][0],
            uid,
        )

    dc_id = stable_id("dc", "Default")
    await conn.execute(
        """INSERT INTO ov_datacenters(id, name, description, status, version_major, version_minor)
           VALUES($1,'Default','Default datacenter','up',4,5)""",
        dc_id,
    )
    cluster_id = stable_id("cluster", "Default")
    await conn.execute(
        """INSERT INTO ov_clusters(id, datacenter_id, name, description)
           VALUES($1,$2,'Default','Default cluster')""",
        cluster_id,
        dc_id,
    )
    host_id = stable_id("host", "host01")
    await conn.execute(
        """INSERT INTO ov_hosts(id, cluster_id, name, address, status, memory, cpu_cores)
           VALUES($1,$2,'host01','192.168.1.10','up',$3,16)""",
        host_id,
        cluster_id,
        128 * 1024**3,
    )
    net_id = stable_id("net", "ovirtmgmt")
    await conn.execute(
        """INSERT INTO ov_networks(id, datacenter_id, name, description)
           VALUES($1,$2,'ovirtmgmt','Management network')""",
        net_id,
        dc_id,
    )
    profile_id = stable_id("vnic", "ovirtmgmt")
    await conn.execute(
        "INSERT INTO ov_vnic_profiles(id, network_id, name) VALUES($1,$2,'ovirtmgmt')",
        profile_id,
        net_id,
    )
    sd_id = stable_id("sd", "data1")
    await conn.execute(
        """INSERT INTO ov_storage_domains(id, name, type, storage_type, status, available, used)
           VALUES($1,'data1','data','nfs','active',$2,$3)""",
        sd_id,
        2 * 1024**4,
        100 * 1024**3,
    )
    await conn.execute(
        """INSERT INTO ov_storage_domain_attachments(id, storage_domain_id, datacenter_id, status)
           VALUES($1,$2,$3,'active')""",
        stable_id("sda", "data1"),
        sd_id,
        dc_id,
    )
    await conn.execute(
        """INSERT INTO ov_storage_connections(id, type, address, path)
           VALUES($1,'nfs','nfs.lab.local','/export/data1')""",
        stable_id("sc", "data1"),
    )
    blank_id = stable_id("template", "Blank")
    await conn.execute(
        """INSERT INTO ov_templates(id, cluster_id, name, description, status, memory)
           VALUES($1,$2,'Blank','Blank template','ok',$3)""",
        blank_id,
        cluster_id,
        1024**3,
    )
    # One sample VM
    vm_id = stable_id("vm", "lab-vm-01")
    await conn.execute(
        """INSERT INTO ov_vms(id, cluster_id, template_id, name, description, status,
           memory, cpu_sockets, cpu_cores, cpu_threads, os_type, type)
           VALUES($1,$2,$3,'lab-vm-01','Sample VM','down',$4,1,2,1,'rhel_8x64','server')""",
        vm_id,
        cluster_id,
        blank_id,
        2 * 1024**3,
    )
    disk_id = stable_id("disk", "lab-vm-01")
    await conn.execute(
        """INSERT INTO ov_disks(id, name, provisioned_size, actual_size, storage_domain_id)
           VALUES($1,'lab-vm-01_Disk1',$2,$2,$3)""",
        disk_id,
        20 * 1024**3,
        sd_id,
    )
    await conn.execute(
        """INSERT INTO ov_disk_attachments(id, vm_id, disk_id, bootable)
           VALUES($1,$2,$3,true)""",
        stable_id("da", "lab-vm-01"),
        vm_id,
        disk_id,
    )
    await conn.execute(
        """INSERT INTO ov_nics(id, vm_id, name, mac_address, vnic_profile_id)
           VALUES($1,$2,'nic1','00:1a:4a:16:01:01',$3)""",
        stable_id("nic", "lab-vm-01"),
        vm_id,
        profile_id,
    )
    await conn.execute(
        "INSERT INTO ov_bookmarks(id, name, value) VALUES($1,'AllVMs','Vms:')",
        stable_id("bm", "AllVMs"),
    )
    await conn.execute(
        """INSERT INTO ov_events(code, severity, description, user_id, vm_id)
           VALUES(1,'normal','Engine started',$1,$2)""",
        admin_id,
        vm_id,
    )
    await conn.execute(
        "INSERT INTO ov_groups(id, domain_id, name) VALUES($1,$2,'engine-admins')",
        stable_id("group", "engine-admins"),
        domain_id,
    )
    await conn.execute(
        "INSERT INTO ov_tags(id, name, description) VALUES($1,'lab','Lab tag')",
        stable_id("tag", "lab"),
    )
    job_id = stable_id("job", "seed-1")
    await conn.execute(
        """INSERT INTO ov_jobs(id, description, status, owner_id)
           VALUES($1,'Seed inventory job','finished',$2)""",
        job_id,
        admin_id,
    )
    await conn.execute(
        """INSERT INTO ov_job_steps(id, job_id, description, status, type, number)
           VALUES($1,$2,'Finish seed','finished','executing',1)""",
        stable_id("step", "seed-1"),
        job_id,
    )
    # Surface-complete sample objects (generic collections)
    for collection, name in (
        ("instancetypes", "Large"),
        ("macpools", "Default"),
        ("schedulingpolicies", "evenly_distributed"),
        ("schedulingpolicies", "power_saving"),
        ("schedulingpolicies", "vm_evenly_distributed"),
        ("schedulingpolicyunits", "EvenlyDistributed"),
        ("clusterlevels", "4.5"),
        ("icons", "default"),
        ("operatingsystems", "rhel_8x64"),
        ("networkfilters", "vdsm-no-mac-spoofing"),
        ("vmpools", "pool-demo"),
        ("affinitylabels", "label-a"),
        ("katelloerrata", "RHSA-2024:0001"),
        ("externalhostproviders", "foreman-lab"),
        ("openstacknetworkproviders", "ovn-provider"),
        ("openstackimageproviders", "glance-lab"),
        ("openstackvolumeproviders", "cinder-lab"),
        ("imagetransfers", "transfer-1"),
    ):
        await conn.execute(
            """INSERT INTO ov_api_objects(id, collection, name, status, data)
               VALUES($1,$2,$3,'ok',$4::jsonb)
               ON CONFLICT (id) DO NOTHING""",
            stable_id("obj", collection, name),
            collection,
            name,
            json.dumps({"name": name, "description": f"seed {collection}"}),
        )

    from app.ovirt.settings import seed_engine_options

    await seed_engine_options(conn)

    # Nested entity links + resource permissions (avoid empty subcollection GETs)
    from app.ovirt.seed_nested import seed_nested_for_inventory

    tag_id = stable_id("tag", "lab")
    await conn.execute(
        """INSERT INTO ov_tag_assignments(id, tag_id, object_type, object_id)
           VALUES($1,$2,'vm',$3) ON CONFLICT DO NOTHING""",
        stable_id("ta", "lab", "lab-vm-01"),
        tag_id,
        vm_id,
    )
    await conn.execute(
        """INSERT INTO ov_snapshots(id, vm_id, description, status)
           VALUES($1,$2,'seed-snapshot','ok')""",
        stable_id("snap", "lab-vm-01", "1"),
        vm_id,
    )
    await conn.execute(
        """INSERT INTO ov_quotas(id, datacenter_id, name, description)
           VALUES($1,$2,'Default','Default quota')""",
        stable_id("quota", "Default"),
        dc_id,
    )
    await conn.execute(
        """INSERT INTO ov_affinity_groups(id, cluster_id, name, enforcing, positive)
           VALUES($1,$2,'web-affinity',true,true)""",
        stable_id("ag", "Default"),
        cluster_id,
    )
    user_ids = [
        r["id"]
        for r in await conn.fetch("SELECT id FROM ov_users ORDER BY name")
    ]
    group_ids = [r["id"] for r in await conn.fetch("SELECT id FROM ov_groups ORDER BY name")]
    await seed_nested_for_inventory(
        conn,
        admin_user_id=admin_id,
        role_user_id=roles[1][0],
        datacenter_ids=[dc_id],
        cluster_ids=[cluster_id],
        host_ids=[host_id],
        network_ids=[net_id],
        storage_domain_ids=[sd_id],
        template_ids=[blank_id],
        vm_ids=[vm_id],
        disk_ids=[disk_id],
        tag_ids=[tag_id],
        user_ids=user_ids,
        group_ids=group_ids,
    )

    await conn.execute(
        "INSERT INTO ov_demo_meta(key, value) VALUES('profile', $1)", MINIMAL_PROFILE
    )
    return {
        "profile": MINIMAL_PROFILE,
        "vms": 1,
        "hosts": 1,
        "datacenters": 1,
        "users": 4,
    }


async def ovirt_demo_summary(conn: Connection) -> dict[str, Any]:
    from app.ovirt.demo_datacenter import CLUSTER_SIZES, DEMO_PROFILES

    profile = await conn.fetchval("SELECT value FROM ov_demo_meta WHERE key='profile'")
    active = profile or MINIMAL_PROFILE
    size = CLUSTER_SIZES.get(active) or (
        CLUSTER_SIZES["large"] if active == "demo" else None
    )
    return {
        "profile": active,
        "loaded": active in DEMO_PROFILES,
        "size": size.name if size else None,
        "size_hosts": size.hosts if size else None,
        "size_vms": size.vms if size else None,
        "vms": await conn.fetchval("SELECT count(*) FROM ov_vms") or 0,
        "hosts": await conn.fetchval("SELECT count(*) FROM ov_hosts") or 0,
        "datacenters": await conn.fetchval("SELECT count(*) FROM ov_datacenters") or 0,
        "clusters": await conn.fetchval("SELECT count(*) FROM ov_clusters") or 0,
        "disks": await conn.fetchval("SELECT count(*) FROM ov_disks") or 0,
        "networks": await conn.fetchval("SELECT count(*) FROM ov_networks") or 0,
        "storage_domains": await conn.fetchval("SELECT count(*) FROM ov_storage_domains") or 0,
        "templates": await conn.fetchval("SELECT count(*) FROM ov_templates") or 0,
        "users": await conn.fetchval("SELECT count(*) FROM ov_users") or 0,
        "events": await conn.fetchval("SELECT count(*) FROM ov_events") or 0,
        "jobs": await conn.fetchval("SELECT count(*) FROM ov_jobs") or 0,
    }
