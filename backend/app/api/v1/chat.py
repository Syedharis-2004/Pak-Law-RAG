"""
PakLaw AI — Conversational Chat Router

Handles chat sessions, streaming responses, and message bookmark management.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.dependencies.auth import get_current_user, get_user_repository
from app.models.user import User
from app.repositories.conversation import ConversationRepository
from app.schemas.chat import (
    BookmarkRequest,
    ChatRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    MessageFeedbackRequest,
)
from app.services.chat import ChatService

router = APIRouter(prefix="/chat", tags=["Conversational AI"])


async def get_conversation_repository(
    db = Depends(get_user_repository)
) -> ConversationRepository:
    from app.models.conversation import Conversation
    return ConversationRepository(Conversation, db.db)


async def get_chat_service(
    repo: Annotated[ConversationRepository, Depends(get_conversation_repository)]
) -> ChatService:
    return ChatService(repo)


@router.post("/query")
async def chat_query(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
):
    """
    Query the AI Legal Copilot.
    Supports standard responses and SSE (Server-Sent Events) streaming.
    """
    if request.stream:
        return StreamingResponse(
            chat_service.stream_chat(request, current_user.id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    
    # Synchronous query helper (uses streaming generator internally and formats response)
    chunks = []
    async for chunk in chat_service.stream_chat(request, current_user.id):
        if chunk.startswith("data: "):
            try:
                data = chunk[6:].strip()
                chunks.append(data)
            except Exception:
                pass
    return {"response": chunks}


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """List conversation threads for the current user."""
    return await chat_service.list_conversations(current_user.id, page, page_size)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Retrieve full history of a conversation thread including messages."""
    return await chat_service.get_conversation_detail(conversation_id, current_user.id)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Delete a conversation history thread."""
    await chat_service.delete_conversation(conversation_id, current_user.id)


@router.post("/bookmarks", status_code=status.HTTP_201_CREATED)
async def bookmark_message(
    request: BookmarkRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Bookmark an AI response for future reference."""
    bookmark_data = {
        "user_id": current_user.id,
        "message_id": request.message_id,
        "title": request.title,
        "note": request.note,
        "tags": request.tags,
    }
    return await chat_service.conversation_repo.create_bookmark(bookmark_data)


@router.delete("/bookmarks/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bookmark(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Remove a message bookmark."""
    success = await chat_service.conversation_repo.remove_bookmark(current_user.id, message_id)
    if not success:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Bookmark for message", str(message_id))


@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def submit_feedback(
    request: MessageFeedbackRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Submit quality ratings and text feedback for AI responses."""
    msg = await chat_service.conversation_repo.get_message(request.message_id)
    if not msg:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Message", str(request.message_id))
    
    msg.user_rating = request.rating
    msg.user_feedback = request.feedback
    await chat_service.conversation_repo.db.flush()
