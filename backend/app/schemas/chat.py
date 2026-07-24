"""
PakLaw AI — Chat Pydantic Schemas
"""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.conversation import ConversationMode, MessageRole


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: uuid.UUID | None = None
    mode: ConversationMode = ConversationMode.CHAT
    language: str | None = None
    document_ids: list[uuid.UUID] | None = None
    stream: bool = True


class CitationResponse(BaseModel):
    id: uuid.UUID
    citation_number: int
    document_title: str
    section_number: str | None
    section_title: str | None
    page_number: int | None
    excerpt: str | None
    relevance_score: float | None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    language: str
    model: str | None
    confidence_score: float | None
    tokens_used: int | None
    latency_ms: int | None
    suggested_questions: list[str] | None
    citations: list[CitationResponse] = []
    is_bookmarked: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    mode: ConversationMode
    language: str
    total_messages: int
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    page: int
    page_size: int


class ConversationDetailResponse(BaseModel):
    conversation: ConversationResponse
    messages: list[MessageResponse]


class StreamChunk(BaseModel):
    """Server-sent event chunk for streaming responses."""
    type: str  # "token" | "citation" | "question" | "done" | "error"
    content: str | None = None
    citations: list[CitationResponse] | None = None
    suggested_questions: list[str] | None = None
    confidence_score: float | None = None
    message_id: uuid.UUID | None = None
    error: str | None = None


class BookmarkRequest(BaseModel):
    message_id: uuid.UUID
    title: str | None = Field(None, max_length=500)
    note: str | None = None
    tags: list[str] | None = None


class MessageFeedbackRequest(BaseModel):
    message_id: uuid.UUID
    rating: int = Field(..., ge=1, le=5)
    feedback: str | None = Field(None, max_length=1000)
