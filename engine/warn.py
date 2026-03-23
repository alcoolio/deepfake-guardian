"""Warning and escalation system.

Tracks violation counts per (user, group) pair and maps the count to an
escalation action:

  count = 1  →  ``notice``               (first offence: educational message)
  count = 2  →  ``admin_notification``   (repeat: alert group admins)
  count ≥ 3  →  ``supervisor_escalation``(persistent: report to supervisor)

Note: This module is named ``warn.py`` (not ``warnings.py``) to avoid
shadowing Python's stdlib ``warnings`` module, which is loaded at interpreter
startup and takes precedence in ``sys.modules``.

API endpoints (mounted at ``/warnings``)
-----------------------------------------
POST /warnings/record           — record a violation, return escalation action
GET  /warnings/{user_id_hash}   — fetch all warning records for a user
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from db_models import UserWarning
from gdpr import hash_id

logger = structlog.get_logger()

warnings_router = APIRouter(prefix="/warnings", tags=["warnings"])

EscalationAction = Literal["notice", "admin_notification", "supervisor_escalation"]

_SUPERVISOR_THRESHOLD = 3


def escalation_action(count: int) -> EscalationAction:
    """Map a cumulative violation count to the appropriate escalation action."""
    if count >= _SUPERVISOR_THRESHOLD:
        return "supervisor_escalation"
    if count >= 2:
        return "admin_notification"
    return "notice"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class RecordViolationRequest(BaseModel):
    user_id: str
    group_id: str
    platform: str = "unknown"
    reasons: list[str] = []


class ViolationResponse(BaseModel):
    user_id_hash: str
    group_id_hash: str
    warning_count: int
    action: EscalationAction


class WarningRecord(BaseModel):
    user_id_hash: str
    group_id_hash: str
    platform: str
    warning_count: int
    last_warning: str | None
    action: EscalationAction


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@warnings_router.post("/record", response_model=ViolationResponse)
async def record_violation(
    body: RecordViolationRequest,
    session: AsyncSession = Depends(get_session),
) -> ViolationResponse:
    """Increment the violation counter for a (user, group) pair.

    Creates a new UserWarning row on first violation.  Returns the updated
    count and the escalation action the bot should take.
    """
    now = datetime.now(tz=timezone.utc)
    user_hash = hash_id(body.platform, body.user_id)
    group_hash = hash_id(body.platform, body.group_id)

    row = (
        await session.execute(
            select(UserWarning).where(
                UserWarning.user_id_hash == user_hash,
                UserWarning.group_id_hash == group_hash,
            )
        )
    ).scalar_one_or_none()

    if row is None:
        row = UserWarning(
            user_id_hash=user_hash,
            group_id_hash=group_hash,
            platform=body.platform,
            warning_count=0,
            level=0,
        )
        session.add(row)

    row.warning_count += 1
    row.last_warning = now
    row.last_reason = json.dumps(body.reasons)
    action = escalation_action(row.warning_count)
    row.level = row.warning_count

    await session.commit()

    logger.info(
        "warning_recorded",
        user_hash=user_hash[:8] + "…",
        group_hash=group_hash[:8] + "…",
        count=row.warning_count,
        action=action,
    )

    return ViolationResponse(
        user_id_hash=user_hash,
        group_id_hash=group_hash,
        warning_count=row.warning_count,
        action=action,
    )


@warnings_router.get("/{user_id_hash}", response_model=list[WarningRecord])
async def get_user_warnings(
    user_id_hash: str,
    session: AsyncSession = Depends(get_session),
) -> list[WarningRecord]:
    """Retrieve all warning records for a user across groups (by pre-hashed ID)."""
    rows = (
        await session.execute(
            select(UserWarning).where(UserWarning.user_id_hash == user_id_hash)
        )
    ).scalars().all()

    return [
        WarningRecord(
            user_id_hash=row.user_id_hash,
            group_id_hash=row.group_id_hash,
            platform=row.platform,
            warning_count=row.warning_count,
            last_warning=row.last_warning.isoformat() if row.last_warning else None,
            action=escalation_action(row.warning_count),
        )
        for row in rows
    ]
