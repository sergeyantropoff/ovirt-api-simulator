"""Async job/task helpers for Engine actions — rows are always loaded from Postgres."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from asyncpg import Connection
from fastapi import Request, Response

from app.ovirt.repr import action_entity, job_entity
from app.ovirt.serialize import respond
from app.ovirt.settings import (
    OPT_DEFAULT_ACTION_STATUS,
    OPT_DEFAULT_JOB_STATUS_COMPLETE,
    OPT_DEFAULT_JOB_STATUS_STARTED,
    OPT_DEFAULT_JOB_STEP_TYPE,
    option_value,
)


async def create_job(
    conn: Connection,
    *,
    description: str,
    owner_id: Any = None,
    auto_complete: bool = True,
    action_status: str | None = None,
) -> dict[str, Any]:
    job_id = uuid4()
    now = datetime.now(UTC)
    finished = await option_value(conn, OPT_DEFAULT_JOB_STATUS_COMPLETE)
    started = await option_value(conn, OPT_DEFAULT_JOB_STATUS_STARTED)
    status = finished if auto_complete else started
    ended = now if auto_complete else None
    if action_status is None:
        action_status = await option_value(conn, OPT_DEFAULT_ACTION_STATUS)
    step_type = await option_value(conn, OPT_DEFAULT_JOB_STEP_TYPE)
    await conn.execute(
        """INSERT INTO ov_jobs(id, description, status, started, ended, owner_id, data)
           VALUES($1, $2, $3, $4, $5, $6, $7::jsonb)""",
        job_id,
        description,
        status,
        now,
        ended,
        owner_id,
        json.dumps({"action_status": action_status}),
    )
    step_id = uuid4()
    await conn.execute(
        """INSERT INTO ov_job_steps(id, job_id, description, status, type, number, started, ended)
           VALUES($1, $2, $3, $4, $5, 1, $6, $7)""",
        step_id,
        job_id,
        description,
        status,
        step_type,
        now,
        ended,
    )
    row = await conn.fetchrow("SELECT * FROM ov_jobs WHERE id=$1", job_id)
    return job_entity(row)


async def complete_job(conn: Connection, job_id: str, *, status: str | None = None) -> None:
    now = datetime.now(UTC)
    if status is None:
        status = await option_value(conn, OPT_DEFAULT_JOB_STATUS_COMPLETE)
    await conn.execute(
        "UPDATE ov_jobs SET status=$2, ended=$3 WHERE id=$1::uuid",
        job_id,
        status,
        now,
    )
    await conn.execute(
        "UPDATE ov_job_steps SET status=$2, ended=$3 WHERE job_id=$1::uuid",
        job_id,
        status,
        now,
    )


async def respond_action(
    request: Request,
    conn: Connection,
    *,
    description: str,
    owner_id: Any = None,
    auto_complete: bool = True,
) -> Response:
    """Persist a job and return an action entity built solely from the DB row."""

    job = await create_job(
        conn, description=description, owner_id=owner_id, auto_complete=auto_complete
    )
    row = await conn.fetchrow("SELECT * FROM ov_jobs WHERE id=$1::uuid", job["id"])
    return respond(request, element="action", data=action_entity(row))
