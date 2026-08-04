"""
PakLaw AI — Research Report Repository

Handles database operations for ResearchReport.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select

from app.models.research import ResearchReport
from app.repositories.base import BaseRepository


class ResearchRepository(BaseRepository[ResearchReport]):
    """Research repository for managing AI-generated legal research reports."""

    model_class = ResearchReport

    async def get_user_reports(
        self, user_id: uuid.UUID, *, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[ResearchReport], int]:
        """Fetch all active research reports for a user with total count."""
        query = select(ResearchReport).where(
            ResearchReport.user_id == user_id, not ResearchReport.is_deleted
        )

        # Total count
        from sqlalchemy import func

        count_query = select(func.count(ResearchReport.id)).where(
            ResearchReport.user_id == user_id, not ResearchReport.is_deleted
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Results
        query = (
            query.order_by(ResearchReport.is_pinned.desc(), ResearchReport.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all(), total
