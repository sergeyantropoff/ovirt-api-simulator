"""Application resource ownership."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Protocol

from fastapi import FastAPI

from app.config import Settings
from app.db.pool import AsyncpgDatabase, Database

DatabaseFactory = Callable[[Settings], Database]
Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


class LifespanWorker(Protocol):
    async def run(self) -> None: ...

    def stop(self) -> None: ...


WorkerFactory = Callable[[Database], LifespanWorker]


def create_lifespan(
    settings: Settings,
    database_factory: DatabaseFactory,
    worker_factories: tuple[WorkerFactory, ...] = (),
) -> Lifespan:
    """Build a lifespan context so tests can inject a database implementation."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = database_factory(settings)
        await database.connect()
        app.state.database = database
        if isinstance(database, AsyncpgDatabase):
            from app.ovirt.demo_datacenter import DEMO_PROFILE
            from app.ovirt.seed import seed_ovirt
            from app.ovirt.settings import seed_engine_options

            async with database.pool.acquire() as connection:
                try:
                    profile = await connection.fetchval(
                        "SELECT value FROM ov_demo_meta WHERE key = 'profile'"
                    )
                except Exception:
                    profile = None
                if profile != DEMO_PROFILE:
                    await seed_ovirt(connection)
                else:
                    # Keep Engine options current without wiping demo inventory.
                    await seed_engine_options(connection)
        workers = tuple(factory(database) for factory in worker_factories)
        worker_tasks = tuple(asyncio.create_task(worker.run()) for worker in workers)
        try:
            yield
        finally:
            for worker in workers:
                worker.stop()
            if worker_tasks:
                await asyncio.gather(*worker_tasks)
            await database.close()

    return lifespan


def default_database_factory(settings: Settings) -> Database:
    """Create the production asyncpg adapter."""

    return AsyncpgDatabase(settings)
