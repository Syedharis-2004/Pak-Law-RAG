"""
PakLaw AI — Conversation Repository

Handles database operations for Conversations, Messages, Citations, and Bookmarks.
"""

import uuid
from collections.abc import Sequence
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.conversation import Bookmark, Citation, Conversation, Message
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Conversation repository for managing threads, messages, and citations."""

    async def get_user_conversations(
        self, user_id: uuid.UUID, *, skip: int = 0, limit: int = 50
    ) -> tuple[Sequence[Conversation], int]:
        """Fetch all active conversations for a user with total count."""
        query = select(Conversation).where(
            Conversation.user_id == user_id, Conversation.is_deleted == False
        )

        # Get total count
        from sqlalchemy import func
        count_query = select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id, Conversation.is_deleted == False
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results
        query = (
            query.order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_with_messages(self, id: uuid.UUID) -> Conversation | None:
        """Fetch a conversation and its messages with citations."""
        query = (
            select(Conversation)
            .where(Conversation.id == id, Conversation.is_deleted == False)
            .options(
                selectinload(Conversation.messages).selectinload(Message.citations)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ── Message Operations ────────────────────────────────────
    async def create_message(self, message_data: dict) -> Message:
        """Create a new message in a conversation thread."""
        message = Message(**message_data)
        self.db.add(message)
        await self.db.flush()
        return message

    async def get_message(self, message_id: uuid.UUID) -> Message | None:
        """Fetch a message by ID with its citations."""
        query = (
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.citations))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ── Citation Operations ───────────────────────────────────
    async def create_citation(self, citation_data: dict) -> Citation:
        """Create a source citation attached to a message."""
        citation = Citation(**citation_data)
        self.db.add(citation)
        await self.db.flush()
        return citation

    # ── Bookmarks ─────────────────────────────────────────────
    async def create_bookmark(self, bookmark_data: dict) -> Bookmark:
        """Create a message bookmark."""
        bookmark = Bookmark(**bookmark_data)
        self.db.add(bookmark)
        await self.db.flush()
        return bookmark

    async def get_user_bookmarks(
        self, user_id: uuid.UUID, *, skip: int = 0, limit: int = 50
    ) -> Sequence[Bookmark]:
        """Fetch all bookmarked items for a user."""
        query = (
            select(Bookmark)
            .where(Bookmark.user_id == user_id)
            .order_by(Bookmark.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def remove_bookmark(self, user_id: uuid.UUID, message_id: uuid.UUID) -> bool:
        """Remove a bookmark for a specific message and user."""
        query = select(Bookmark).where(
            Bookmark.user_id == user_id, Bookmark.message_id == message_id
        )
        result = await self.db.execute(query)
        bookmark = result.scalar_one_or_none()
        if bookmark:
            await self.db.delete(bookmark)
            await self.db.flush()
            return True
        return False
