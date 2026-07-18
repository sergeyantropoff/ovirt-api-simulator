"""Deterministic UUIDs for seed data."""

from __future__ import annotations

from uuid import UUID, uuid5

NAMESPACE = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def stable_id(*parts: str) -> UUID:
    return uuid5(NAMESPACE, ":".join(parts))


def stable_str(*parts: str) -> str:
    return str(stable_id(*parts))
