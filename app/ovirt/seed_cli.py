"""CLI: python -m app.ovirt.seed_cli [--profile minimal|small|large|big|demo]."""

from __future__ import annotations

import argparse
import asyncio
import json
import os

import asyncpg

from app.ovirt.demo_datacenter import DEMO_PROFILES, normalize_cluster_size, seed_ovirt_demo
from app.ovirt.seed import seed_ovirt


async def _run(profile: str) -> dict:
    dsn = os.environ.get(
        "DATABASE_URL",
        "postgresql://ovirt:ovirt@localhost:5432/ovirt_simulator",
    )
    conn = await asyncpg.connect(dsn)
    try:
        if profile == "minimal":
            result = await seed_ovirt(conn)
        elif profile in DEMO_PROFILES or profile in {"small", "large", "big"}:
            result = await seed_ovirt_demo(conn, size=normalize_cluster_size(profile))
        else:
            raise SystemExit(
                f"unknown profile {profile!r}; expected minimal|small|large|big|demo"
            )
        return result
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed oVirt Engine simulator")
    parser.add_argument(
        "--profile",
        default=os.environ.get("SEED_PROFILE", "minimal"),
        help="minimal | small | large | big | demo (demo→large)",
    )
    args = parser.parse_args()
    result = asyncio.run(_run(args.profile))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
