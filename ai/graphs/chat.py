"""
PakLaw AI — Chat Graph Workflow (LangGraph)

Defines a multi-step conversational agent workflow.
Falls back to direct Gemini generation if Qdrant / embeddings are unavailable.
"""

import logging
from typing import Any, Dict, List, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    query: str
    rewritten_query: str
    language: str
    document_ids: List[str] | None
    conversation_id: str
    retrieved_documents: List[Any]  # Nodes retrieved
    response_text: str
    confidence_score: float
    suggested_questions: List[str]
    token: str  # For streaming output


def _get_llm(temperature: float | None = None) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature if temperature is not None else settings.GEMINI_TEMPERATURE,
        max_tokens=settings.GEMINI_MAX_TOKENS,
    )


async def rewrite_query(state: AgentState) -> Dict:
    """Rewrite and expand raw query for better dense/sparse vector match."""
    try:
        llm = _get_llm(temperature=0.2)
        prompt = (
            "Optimize and expand the following Pakistani legal search query for "
            "keyword and semantic vector matching. Maintain intent and return ONLY "
            f"the optimized search text: {state['query']}"
        )
        response = await llm.ainvoke(prompt)
        return {"rewritten_query": response.content.strip()}
    except Exception as e:
        logger.warning(f"Query rewriting failed, using original: {e}")
        return {"rewritten_query": state["query"]}


async def retrieve(state: AgentState) -> Dict:
    """Run hybrid search against Qdrant. Fast-fails if Qdrant is unreachable."""
    import socket

    # Quick TCP probe — avoids loading BGE-M3 model (~500 MB) when Qdrant is down
    qdrant_available = False
    try:
        sock = socket.create_connection(
            (settings.QDRANT_HOST, settings.QDRANT_PORT), timeout=1.0
        )
        sock.close()
        qdrant_available = True
    except Exception:
        pass

    if not qdrant_available:
        logger.info("Qdrant not reachable — skipping retrieval, using direct Gemini generation")
        return {"retrieved_documents": []}

    try:
        from ai.pipelines.retrieval import HybridRetriever
        retriever = HybridRetriever()
        filters = {}
        if state.get("document_ids"):
            filters["document_id"] = state["document_ids"]
        query_to_search = state.get("rewritten_query") or state["query"]
        nodes = await retriever.retrieve(
            query=query_to_search,
            filters=filters,
            top_k=settings.RETRIEVAL_TOP_K,
        )
        return {"retrieved_documents": nodes}
    except Exception as e:
        logger.warning(f"Retrieval pipeline failed: {e}")
        return {"retrieved_documents": []}


async def generate(state: AgentState) -> Dict:
    """Generate final localized legal answer using Google Gemini."""
    llm = _get_llm()

    retrieved_docs = state.get("retrieved_documents") or []

    if retrieved_docs:
        # RAG mode — use retrieved context
        context_list = []
        for doc in retrieved_docs:
            node = getattr(doc, "node", doc)
            meta = getattr(node, "metadata", {})
            text = getattr(node, "text", "") or getattr(node, "get_content", lambda: "")()
            context_list.append(
                f"Doc: {meta.get('title', 'Legal Document')} "
                f"(Section: {meta.get('section_number', 'N/A')}, "
                f"Page: {meta.get('page_number', 'N/A')})\n"
                f"Content: {text}"
            )
        context_str = "\n\n---\n\n".join(context_list)

        from ai.prompts.system import SYSTEM_CHAT_PROMPT
        prompt = SYSTEM_CHAT_PROMPT.format(
            context=context_str,
            chat_history="",
            query=state["query"],
        )
        confidence = 0.9
    else:
        # Fallback mode — direct Gemini with Pakistani law expertise
        lang = state.get("language", "en")
        lang_instruction = (
            "Respond in Urdu." if lang == "ur"
            else "Respond in Roman Urdu." if lang == "ro"
            else "Respond in English."
        )
        prompt = (
            "You are PakLaw AI, an expert legal copilot specializing in Pakistani law "
            "(Constitution of Pakistan 1973, PPC, CPC, CRPC, Contract Act, Family Laws, "
            "Company Law, Tax Law, and all major statutes). "
            f"{lang_instruction} "
            "Provide a clear, accurate, well-structured legal answer. "
            "Cite relevant articles, sections, and case law where applicable. "
            "Be thorough but concise.\n\n"
            f"Legal Question: {state['query']}\n\n"
            "PakLaw AI Answer:"
        )
        confidence = 0.75

    response = await llm.ainvoke(prompt)
    response_text = response.content

    # Generate follow-up questions
    suggested = []
    try:
        suggested_prompt = (
            "Based on the following Pakistani legal response, suggest exactly 3 short, "
            "relevant follow-up questions a lawyer might ask next. "
            "Return ONLY the 3 questions as a numbered list (1. 2. 3.), nothing else:\n\n"
            f"{response_text[:1000]}"
        )
        suggested_res = await llm.ainvoke(suggested_prompt)
        for line in suggested_res.content.split("\n"):
            line = line.strip().lstrip("123.-)*").strip()
            if line and len(line) > 10:
                suggested.append(line)
        suggested = suggested[:3]
    except Exception as e:
        logger.warning(f"Suggested questions generation failed: {e}")

    return {
        "response_text": response_text,
        "token": response_text,
        "confidence_score": confidence,
        "suggested_questions": suggested,
    }


def get_chat_graph():
    """Builds and compiles the conversational RAG graph workflow."""
    workflow = StateGraph(AgentState)

    workflow.add_node("rewrite_query", rewrite_query)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)

    workflow.set_entry_point("rewrite_query")
    workflow.add_edge("rewrite_query", "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()
