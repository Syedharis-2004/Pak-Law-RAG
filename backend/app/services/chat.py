"""
PakLaw AI — Conversational RAG Service

Manages streaming chat interactions with the AI Copilot. Utilizes
LangGraph to invoke retrieval, rewrite, and generation steps.
"""

import json
import uuid
from collections.abc import AsyncGenerator

from app.core.exceptions import NotFoundError
from app.models.conversation import Conversation, ConversationMode
from app.repositories.conversation import ConversationRepository
from app.schemas.chat import (
    ChatRequest,
    CitationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
    StreamChunk,
)


class ChatService:
    """Service layer for streaming conversational RAG and thread history."""

    def __init__(self, conversation_repo: ConversationRepository) -> None:
        self.conversation_repo = conversation_repo

    async def get_or_create_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None = None,
        mode: ConversationMode = ConversationMode.CHAT,
        language: str = "en",
    ) -> Conversation:
        """Get existing conversation or create a new one."""
        if conversation_id:
            convo = await self.conversation_repo.get(conversation_id)
            if not convo or convo.is_deleted:
                raise NotFoundError("Conversation", str(conversation_id))
            return convo

        # Create new
        convo_in = {
            "user_id": user_id,
            "mode": mode,
            "language": language,
            "title": "New Legal Query",
        }
        return await self.conversation_repo.create(convo_in)

    async def list_conversations(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> ConversationListResponse:
        """Fetch user's conversation list with pagination."""
        skip = (page - 1) * page_size
        convos, total = await self.conversation_repo.get_user_conversations(
            user_id, skip=skip, limit=page_size
        )
        items = [ConversationResponse.from_orm(c) for c in convos]
        return ConversationListResponse(
            items=items, total=total, page=page, page_size=page_size
        )

    async def get_conversation_detail(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConversationDetailResponse:
        """Fetch complete conversation detail including messages and citations."""
        convo = await self.conversation_repo.get_with_messages(conversation_id)
        if not convo or convo.is_deleted or convo.user_id != user_id:
            raise NotFoundError("Conversation", str(conversation_id))

        convo_res = ConversationResponse.from_orm(convo)
        messages_res = [MessageResponse.from_orm(m) for m in convo.messages]

        return ConversationDetailResponse(conversation=convo_res, messages=messages_res)

    async def delete_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Soft delete a conversation thread."""
        convo = await self.conversation_repo.get(conversation_id)
        if not convo or convo.is_deleted or convo.user_id != user_id:
            raise NotFoundError("Conversation", str(conversation_id))
        convo.is_deleted = True
        await self.conversation_repo.db.flush()

    async def stream_chat(
        self, request: ChatRequest, user_id: uuid.UUID
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response using LangGraph.
        Yields Server-Sent Events (SSE) JSON strings.
        """
        try:
            # Ensure conversation exists
            convo = await self.get_or_create_conversation(
                user_id=user_id,
                conversation_id=request.conversation_id,
                mode=request.mode,
                language=request.language or "en",
            )

            # Create user message in DB
            user_msg_in = {
                "conversation_id": convo.id,
                "role": "user",
                "content": request.message,
                "language": request.language or "en",
            }
            await self.conversation_repo.create_message(user_msg_in)
            await self.conversation_repo.db.commit()

            # Initialize LangGraph conversational RAG graph
            from ai.graphs.chat import get_chat_graph
            graph = get_chat_graph()

            # Construct inputs for the graph
            inputs = {
                "query": request.message,
                "language": request.language or "en",
                "document_ids": [str(d) for d in request.document_ids] if request.document_ids else None,
                "conversation_id": str(convo.id),
                "rewritten_query": "",
                "retrieved_documents": [],
                "response_text": "",
                "confidence_score": 0.0,
                "suggested_questions": [],
                "token": "",
            }

            assistant_message_id = uuid.uuid4()
            full_response_text = ""
            citations = []
            confidence_score = 0.8
            suggested_questions = []

            # Stream from LangGraph — each event is a dict of {node_name: state_updates}
            async for event in graph.astream(inputs, stream_mode="updates"):
                # ── Citations from retrieval ──────────────────────
                if "retrieve" in event:
                    nodes = event["retrieve"].get("retrieved_documents", [])
                    citations = []
                    for idx, node_with_score in enumerate(nodes):
                        node = getattr(node_with_score, "node", node_with_score)
                        meta = getattr(node, "metadata", {})
                        text = getattr(node, "text", "") or ""
                        citations.append({
                            "id": str(uuid.uuid4()),
                            "citation_number": idx + 1,
                            "document_title": meta.get("title", "Official Legal Document"),
                            "section_number": meta.get("section_number"),
                            "section_title": meta.get("section_title"),
                            "page_number": meta.get("page_number"),
                            "excerpt": text[:200],
                            "relevance_score": float(getattr(node_with_score, "score", 0.0) or 0.0),
                        })
                    if citations:
                        yield f"data: {json.dumps(StreamChunk(type='citations', citations=citations).model_dump(), default=str)}\n\n"

                # ── Generated response ────────────────────────────
                if "generate" in event:
                    gen_data = event["generate"]
                    # Full response text comes in "token" key (set by graph node)
                    response_text = gen_data.get("token") or gen_data.get("response_text", "")
                    if response_text:
                        full_response_text = response_text
                        # Stream word-by-word for smoother UX
                        words = response_text.split(" ")
                        for i, word in enumerate(words):
                            token = word + (" " if i < len(words) - 1 else "")
                            yield f"data: {json.dumps(StreamChunk(type='token', content=token).model_dump())}\n\n"

                    confidence_score = gen_data.get("confidence_score", 0.8)
                    suggested_questions = gen_data.get("suggested_questions", [])

            # Yield metadata (confidence + follow-up questions)
            yield f"data: {json.dumps(StreamChunk(type='metadata', confidence_score=confidence_score, suggested_questions=suggested_questions).model_dump())}\n\n"

            # Persist assistant message to DB
            if full_response_text:
                assistant_msg_in = {
                    "id": assistant_message_id,
                    "conversation_id": convo.id,
                    "role": "assistant",
                    "content": full_response_text,
                    "language": request.language or "en",
                    "confidence_score": confidence_score,
                    "suggested_questions": suggested_questions,
                }
                await self.conversation_repo.create_message(assistant_msg_in)

                # Persist citations
                for citation in citations:
                    citation_in = {
                        "message_id": assistant_message_id,
                        "citation_number": citation["citation_number"],
                        "document_title": citation["document_title"],
                        "section_number": citation.get("section_number"),
                        "section_title": citation.get("section_title"),
                        "page_number": citation.get("page_number"),
                        "excerpt": citation.get("excerpt", ""),
                        "relevance_score": citation.get("relevance_score", 0.0),
                    }
                    await self.conversation_repo.create_citation(citation_in)

            # Update conversation stats
            convo.total_messages += 2
            convo.title = request.message[:50] + "..." if len(request.message) > 50 else request.message
            await self.conversation_repo.db.commit()

            yield f"data: {json.dumps(StreamChunk(type='done', message_id=assistant_message_id).model_dump(), default=str)}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"I encountered an error processing your request: {type(e).__name__}: {str(e)}"
            yield f"data: {json.dumps(StreamChunk(type='error', content=error_msg).model_dump(), default=str)}\n\n"


