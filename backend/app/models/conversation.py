"""
PakLaw AI — Conversation, Message, and Citation ORM Models

Stores conversation threads, individual messages, AI citations,
and user bookmarks with full conversation memory support.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMode(StrEnum):
    CHAT = "chat"
    RESEARCH = "research"
    CONTRACT_REVIEW = "contract_review"
    DOCUMENT_ANALYSIS = "document_analysis"
    LEGAL_NOTICE = "legal_notice"


class Conversation(Base):
    """A conversation thread between a user and the AI copilot."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False, default="New Conversation")
    mode: Mapped[ConversationMode] = mapped_column(String(50), default=ConversationMode.CHAT)
    language: Mapped[str] = mapped_column(String(10), default="en")

    # Document context (optional — conversation scoped to specific docs)
    scoped_document_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Stats
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")  # type: ignore[name-defined] # noqa: F821
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.id} [{self.mode}]>"


class Message(Base):
    """An individual message within a conversation."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[MessageRole] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")

    # AI metadata (only for assistant messages)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Retrieval metadata
    retrieved_chunk_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    retrieved_document_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    retrieval_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Suggested follow-up questions
    suggested_questions: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # User feedback
    user_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    user_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")
    citations: Mapped[list["Citation"]] = relationship(
        "Citation", back_populates="message", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Message {self.role}/{self.id}>"


class Citation(Base):
    """A source citation attached to an AI response message."""

    __tablename__ = "citations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Citation details
    citation_number: Mapped[int] = mapped_column(Integer, nullable=False)
    document_title: Mapped[str] = mapped_column(String(500), nullable=False)
    section_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    message: Mapped[Message] = relationship("Message", back_populates="citations")

    def __repr__(self) -> str:
        return f"<Citation [{self.citation_number}] {self.document_title[:40]}>"


class Bookmark(Base):
    """User-saved bookmarks for messages and research reports."""

    __tablename__ = "bookmarks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Bookmark {self.id}>"
