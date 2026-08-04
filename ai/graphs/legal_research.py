"""
PakLaw AI — Advanced Legal Research Report Graph

Handles deep legal research reports generation from retrieved statutory collections.
"""

import json
import logging
from typing import Any, TypedDict

from app.core.config import settings
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from ai.prompts.research import RESEARCH_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ── Module-level singleton so BGE-M3 model is loaded only once per process ──
_retriever_instance = None


def _get_retriever():
    """Return a cached HybridRetriever instance (loads BGE-M3 only once)."""
    global _retriever_instance
    if _retriever_instance is None:
        try:
            from ai.pipelines.retrieval import HybridRetriever
            _retriever_instance = HybridRetriever()
            logger.info("HybridRetriever singleton initialised for research graph.")
        except Exception as e:
            logger.warning(f"HybridRetriever init failed: {e}")
    return _retriever_instance


class ResearchState(TypedDict):
    query: str
    language: str
    document_ids: list[str] | None
    include_judgments: bool
    include_amendments: bool
    retrieved_sections: list[Any]
    report_json: dict
    report_markdown: str


async def retrieve_laws(state: ResearchState) -> dict:
    """Retrieve wide set of sections across documents for synthesis."""
    retriever = _get_retriever()
    if retriever is None:
        logger.warning("No retriever available — research graph will use fallback prompt only.")
        return {"retrieved_sections": []}

    filters = {}
    if state.get("document_ids"):
        filters["document_id"] = state["document_ids"]

    # Wide retrieval
    nodes = await retriever.retrieve(
        query=state["query"],
        filters=filters,
        top_k=30,  # Grab a larger pool of potential codes for research mode
    )
    return {"retrieved_sections": nodes}


async def generate_report(state: ResearchState) -> dict:
    """Generate comprehensive structured research report JSON using Groq.
    
    Uses a single LLM call that produces both the structured JSON and the
    Markdown presentation — halving network round-trips vs. two sequential calls.
    """
    llm = ChatGroq(
        model=settings.GROQ_MODEL,
        groq_api_key=settings.GROQ_API_KEY,
        temperature=0.1,
        max_tokens=settings.GROQ_MAX_TOKENS,
        max_retries=2,
    )

    # ── Build context from NodeWithScore objects ────────────────────────────
    context_list = []
    for nws in state.get("retrieved_sections", []):
        node = getattr(nws, "node", nws)
        meta = getattr(node, "metadata", {}) or {}
        text = (
            getattr(node, "text", "")
            or getattr(node, "get_content", lambda: "")()
            or ""
        )
        context_list.append(
            f"Statute: {meta.get('title', 'Legal Document')} | "
            f"Section: {meta.get('section_number', 'N/A')} - "
            f"{meta.get('section_title', 'N/A')}\n"
            f"Content: {text}"
        )

    context_str = (
        "\n\n---\n\n".join(context_list)
        if context_list
        else (
            "No documents retrieved from vector store. "
            "Generate the report from general Pakistani statutory knowledge."
        )
    )

    # ── Single combined prompt: JSON block + Markdown block ────────────────
    # Merging into one call cuts latency by ~50% vs. two sequential ainvoke().
    combined_prompt = f"""{RESEARCH_SYSTEM_PROMPT.format(context=context_str, query=state["query"])}

---

After outputting the JSON above, also produce a MARKDOWN_REPORT section starting with the exact marker:

===MARKDOWN_REPORT===

Convert the JSON into a beautifully styled professional legal research report in Markdown.
Use formal headings, bold statutory citations, numbered sections, and a proper citations list.
Write for Pakistani law practitioners. Do not include the raw JSON in the Markdown section."""

    response = await llm.ainvoke(combined_prompt)
    raw_content = response.content.strip()

    # ── Split JSON and Markdown sections ───────────────────────────────────
    markdown_text = ""
    if "===MARKDOWN_REPORT===" in raw_content:
        json_part, _, markdown_text = raw_content.partition("===MARKDOWN_REPORT===")
        markdown_text = markdown_text.strip()
    else:
        json_part = raw_content

    # Clean JSON code-fence wrapping
    json_part = json_part.strip()
    if json_part.startswith("```json"):
        json_part = json_part[7:]
    elif json_part.startswith("```"):
        json_part = json_part[3:]
    if json_part.endswith("```"):
        json_part = json_part[:-3]
    json_part = json_part.strip()

    try:
        report_json = json.loads(json_part)
    except Exception:
        logger.warning("Failed to parse research report JSON; using fallback structure.")
        report_json = {
            "title": f"Legal Research Report — {state['query'][:60]}",
            "executive_summary": (
                json_part[:500] if json_part
                else "Report generation encountered a parsing issue."
            ),
            "legal_issues": [],
            "applicable_laws": [],
            "relevant_sections": [],
            "conflicts_detected": [],
            "recommendations": ["Review the raw AI output for analysis."],
            "citations": [],
        }

    # If the model did not output a Markdown section, build a minimal one
    if not markdown_text:
        markdown_text = (
            f"# {report_json.get('title', 'Legal Research Report')}\n\n"
            f"## Executive Summary\n\n{report_json.get('executive_summary', '')}\n\n"
            + "\n\n".join(
                f"- {rec}" for rec in report_json.get("recommendations", [])
            )
        )

    return {"report_json": report_json, "report_markdown": markdown_text}


def get_research_graph():
    """Builds and compiles the advanced legal research graph (always fresh compile)."""
    workflow = StateGraph(ResearchState)

    # Nodes
    workflow.add_node("retrieve_laws", retrieve_laws)
    workflow.add_node("generate_report", generate_report)

    # Edges
    workflow.set_entry_point("retrieve_laws")
    workflow.add_edge("retrieve_laws", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()
