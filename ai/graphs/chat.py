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


def _get_llm(model_name: str | None = None, temperature: float | None = None) -> ChatGoogleGenerativeAI:
    target_model = model_name or settings.GEMINI_MODEL
    return ChatGoogleGenerativeAI(
        model=target_model,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature if temperature is not None else settings.GEMINI_TEMPERATURE,
        max_tokens=settings.GEMINI_MAX_TOKENS,
    )


async def rewrite_query(state: AgentState) -> Dict:
    """Pass query directly to minimize extra LLM latency roundtrips."""
    return {"rewritten_query": state["query"].strip()}


async def retrieve(state: AgentState) -> Dict:
    """Run search against Qdrant (remote or local disk) and MongoDB fallback."""
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
        logger.warning(f"Retrieval pipeline fallback: {e}")
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

    # Main LLM call with rate limit retry & model fallback
    import asyncio
    models_to_try = [settings.GEMINI_MODEL, "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash-001"]
    response_text = ""
    last_error = None

    for m in models_to_try:
        try:
            active_llm = _get_llm(model_name=m)
            response = await active_llm.ainvoke(prompt)
            response_text = response.content
            last_error = None
            break
        except Exception as e:
            last_error = e
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e) or "NOT_FOUND" in str(e):
                logger.warning(f"Model {m} returned quota error, trying fallback model...")
                await asyncio.sleep(1)
                continue
            else:
                raise e

    if last_error and not response_text:
        raise last_error

    # Quick smart follow-up suggestions without extra blocking API delay
    query_text = state['query'].lower()
    if "constitution" in query_text or "writ" in query_text or "199" in query_text:
        suggested = [
            "What are the grounds for High Court jurisdiction under Article 199?",
            "What is the difference between certiorari and mandamus writs?",
            "What precedent cases apply to fundamental rights violation?"
        ]
    elif "contract" in query_text or "agreement" in query_text:
        suggested = [
            "What are the essential elements of a valid contract under Contract Act 1872?",
            "What remedies exist for breach of contract in Pakistan?",
            "How is liquidated damages defined in Pakistani law?"
        ]
    elif "tax" in query_text or "income" in query_text:
        suggested = [
            "What are the key tax appeal procedures in Income Tax Ordinance?",
            "What penalty exists for late filing under FBR rules?",
            "What exemptions apply to IT export services?"
        ]
    else:
        suggested = [
            "What relevant case laws or precedents apply to this legal issue?",
            "What are the procedural steps to file a petition in court?",
            "Which specific statute or act governs this matter?"
        ]

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
