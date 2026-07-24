"""
PakLaw AI — Advanced Legal Research Report Graph

Handles deep legal research reports generation from retrieved statutory collections.
"""

import json
from typing import Any, Dict, List, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from app.core.config import settings
from ai.pipelines.retrieval import HybridRetriever
from ai.prompts.research import RESEARCH_SYSTEM_PROMPT


class ResearchState(TypedDict):
    query: str
    language: str
    document_ids: List[str] | None
    include_judgments: bool
    include_amendments: bool
    retrieved_sections: List[Any]
    report_json: Dict
    report_markdown: str


async def retrieve_laws(state: ResearchState) -> Dict:
    """Retrieve wide set of sections across documents for synthesis."""
    retriever = HybridRetriever()
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


async def generate_report(state: ResearchState) -> Dict:
    """Generate comprehensive structured research report JSON using Gemini Pro."""
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
    )

    # Construct context
    context_list = []
    for doc in state["retrieved_sections"]:
        meta = doc.metadata
        context_list.append(
            f"Statute: {meta.get('title')} | Section: {meta.get('section_number', 'N/A')} - {meta.get('section_title', 'N/A')}\nContent: {doc.text}"
        )
    context_str = "\n\n---\n\n".join(context_list)

    prompt = RESEARCH_SYSTEM_PROMPT.format(
        context=context_str,
        query=state["query"]
    )

    response = await llm.ainvoke(prompt)
    raw_content = response.content.strip()

    # Clean potential json ticks
    if raw_content.startswith("```json"):
        raw_content = raw_content.lstrip("```json").rstrip("```")
    elif raw_content.startswith("```"):
        raw_content = raw_content.lstrip("```").rstrip("```")

    try:
        report_json = json.loads(raw_content)
    except Exception:
        # Fallback dictionary if JSON breaks
        report_json = {
            "title": "Legal Research Report",
            "executive_summary": "Error parsing generated report JSON structure.",
            "legal_issues": [],
            "applicable_laws": [],
            "relevant_sections": [],
            "conflicts_detected": [],
            "recommendations": [],
            "citations": []
        }

    # Generate Markdown Presentation
    markdown_prompt = f"Convert the following structured legal research JSON report into a beautifully-styled, professional, comprehensive markdown research report. Focus on clear typography, bold legal section highlights, and formal citation lists:\n\n{json.dumps(report_json)}"
    markdown_res = await llm.ainvoke(markdown_prompt)

    return {
        "report_json": report_json,
        "report_markdown": markdown_res.content
    }


def get_research_graph():
    """Builds and compiles the advanced legal research graph."""
    workflow = StateGraph(ResearchState)

    # Nodes
    workflow.add_node("retrieve_laws", retrieve_laws)
    workflow.add_node("generate_report", generate_report)

    # Edges
    workflow.set_entry_point("retrieve_laws")
    workflow.add_edge("retrieve_laws", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()
