"""
PakLaw AI — Audit and Analytics Repository

Handles writing audit logs and analytics events.
"""

import uuid
from collections.abc import Sequence
from sqlalchemy import select

from app.models.audit import AnalyticsEvent, AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Audit repository for managing audit trails and analytics events."""

    async def create_audit_log(self, audit_data: dict) -> AuditLog:
        """Log a user or system action (immutable write)."""
        log = AuditLog(**audit_data)
        self.db.add(log)
        await self.db.flush()
        return log

    async def create_analytics_event(self, event_data: dict) -> AnalyticsEvent:
        """Record an analytics event."""
        event = AnalyticsEvent(**event_data)
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_system_audit_logs(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        user_id: uuid.UUID | None = None,
        action: str | None = None,
        resource: str | None = None,
    ) -> tuple[Sequence[AuditLog], int]:
        """Fetch audit logs for system administrators."""
        query = select(AuditLog)

        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource:
            query = query.where(AuditLog.resource == resource)

        # Count
        from sqlalchemy import func
        count_query = select(func.count(AuditLog.id))
        if user_id:
            count_query = count_query.where(AuditLog.user_id == user_id)
        if action:
            count_query = count_query.where(AuditLog.action == action)
        if resource:
            count_query = count_query.where(AuditLog.resource == resource)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all(), total
