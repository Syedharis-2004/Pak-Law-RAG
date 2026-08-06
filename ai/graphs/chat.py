"""
PakLaw AI — Chat Graph Workflow (LangGraph)

Defines a multi-step conversational agent workflow.
Falls back to direct Gemini generation if Qdrant / embeddings are unavailable.
"""

import asyncio
import logging
from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level singletons so the TCP probe + model init only runs once per process.
_retriever_instance = None
_compiled_graph = None
_llm_cache: dict = {}


def _get_retriever():
    global _retriever_instance
    if _retriever_instance is None:
        try:
            from ai.pipelines.retrieval import HybridRetriever
            _retriever_instance = HybridRetriever()
        except Exception as e:
            logger.warning(f"HybridRetriever init failed, retrieval disabled: {e}")
    return _retriever_instance


class AgentState(TypedDict):
    query: str
    rewritten_query: str
    language: str
    document_ids: list[str] | None
    conversation_id: str
    retrieved_documents: list[Any]  # Nodes retrieved
    response_text: str
    confidence_score: float
    suggested_questions: list[str]
    token: str  # For streaming output


def _get_llm(model_name: str | None = None, temperature: float | None = None) -> ChatGroq:
    """Return a cached ChatGroq instance per model to avoid repeated TCP handshakes."""
    target_model = model_name or settings.GROQ_MODEL
    cache_key = (target_model, temperature)
    if cache_key not in _llm_cache:
        _llm_cache[cache_key] = ChatGroq(
            model=target_model,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=temperature if temperature is not None else settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
            max_retries=1,  # Fast fail-fast for quota/auth errors
        )
    return _llm_cache[cache_key]


async def rewrite_query(state: AgentState) -> dict:
    """Pass query directly to minimize extra LLM latency roundtrips."""
    return {"rewritten_query": state["query"].strip()}


async def retrieve(state: AgentState) -> dict:
    """Run search against Qdrant (remote or local disk) and MongoDB fallback."""
    try:
        retriever = _get_retriever()
        if retriever is None:
            return {"retrieved_documents": []}

        filters = {}
        if state.get("document_ids"):
            filters["document_id"] = state["document_ids"]
        query_to_search = state.get("rewritten_query") or state["query"]

        # retriever.retrieve() is async — call it directly.
        # Synchronous Qdrant/embedding calls inside are offloaded
        # via run_in_executor within the retriever itself.
        if asyncio.iscoroutinefunction(retriever.retrieve):
            nodes = await retriever.retrieve(
                query=query_to_search,
                filters=filters,
                top_k=settings.RETRIEVAL_TOP_K,
            )
        else:
            loop = asyncio.get_running_loop()
            nodes = await loop.run_in_executor(
                None,
                lambda: retriever.retrieve(
                    query=query_to_search,
                    filters=filters,
                    top_k=settings.RETRIEVAL_TOP_K,
                ),
            )
        return {"retrieved_documents": nodes}
    except Exception as e:
        logger.warning(f"Retrieval pipeline fallback: {e}")
        return {"retrieved_documents": []}


async def generate(state: AgentState, config: RunnableConfig = None) -> dict:
    """Generate final localized legal answer using Google Gemini."""

    retrieved_docs = state.get("retrieved_documents") or []
    queue = config.get("configurable", {}).get("token_queue") if config else None

    if retrieved_docs:
        # RAG mode — use retrieved context
        context_list = []
        for doc in retrieved_docs:
            node = getattr(doc, "node", doc)
            meta = getattr(node, "metadata", {})
            text = (
                getattr(node, "text", "") or getattr(node, "get_content", lambda: "")()
            )
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
            "Respond in Urdu."
            if lang == "ur"
            else "Respond in Roman Urdu."
            if lang == "ro"
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

    # Groq model fallback chain (fast → lightweight)
    models_to_try = [
        settings.GROQ_MODEL,          # llama-3.3-70b-versatile (primary)
        "llama-3.1-8b-instant",       # fast fallback
        "mixtral-8x7b-32768",         # broad context fallback
        "gemma2-9b-it",               # last resort
    ]
    response_text = ""
    last_error = None

    for m in models_to_try:
        try:
            active_llm = _get_llm(model_name=m)
            # Real-time token streaming via astream
            async for chunk in active_llm.astream(prompt):
                content = chunk.content
                response_text += content
                if queue and content:
                    await queue.put(("token", content))  # Tuple format expected by service layer
            last_error = None
            break
        except Exception as e:
            last_error = e
            if (
                "RESOURCE_EXHAUSTED" in str(e)
                or "429" in str(e)
                or "NOT_FOUND" in str(e)
            ):
                logger.warning(
                    f"Model {m} returned quota error, trying fallback model..."
                )
                await asyncio.sleep(0.1)  # Faster fallback transition
                continue
            else:
                raise

    if last_error and not response_text:
        raise last_error

    # Quick smart follow-up suggestions without extra blocking API delay
    query_text = state["query"].lower()
    if "constitution" in query_text or "writ" in query_text or "199" in query_text:
        suggested = [
            "What are the grounds for High Court jurisdiction under Article 199?",
            "What is the difference between certiorari and mandamus writs?",
            "What precedent cases apply to fundamental rights violation?",
        ]
    elif "contract" in query_text or "agreement" in query_text:
        suggested = [
            "What are the essential elements of a valid contract under Contract Act 1872?",
            "What remedies exist for breach of contract in Pakistan?",
            "How is liquidated damages defined in Pakistani law?",
        ]
    elif "tax" in query_text or "income" in query_text:
        suggested = [
            "What are the key tax appeal procedures in Income Tax Ordinance?",
            "What penalty exists for late filing under FBR rules?",
            "What exemptions apply to IT export services?",
        ]
    else:
        suggested = [
            "What relevant case laws or precedents apply to this legal issue?",
            "What are the procedural steps to file a petition in court?",
            "Which specific statute or act governs this matter?",
        ]

    return {
        "response_text": response_text,
        "token": response_text,
        "confidence_score": confidence,
        "suggested_questions": suggested,
    }


def get_chat_graph():
    """Returns the compiled conversational RAG graph (singleton — compiled once per process)."""
    global _compiled_graph
    if _compiled_graph is None:
        workflow = StateGraph(AgentState)

        workflow.add_node("rewrite_query", rewrite_query)
        workflow.add_node("retrieve", retrieve)
        workflow.add_node("generate", generate)

        workflow.set_entry_point("rewrite_query")
        workflow.add_edge("rewrite_query", "retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        _compiled_graph = workflow.compile()
        logger.info("LangGraph chat graph compiled and cached.")

    return _compiled_graph
