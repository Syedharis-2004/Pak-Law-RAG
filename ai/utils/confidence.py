"""
PakLaw AI — AI Confidence Scorer

Calculates a score based on context relevance and token match statistics.
"""

from llama_index.core.schema import NodeWithScore


def calculate_confidence_score(
    retrieved_nodes: list[NodeWithScore], response_text: str
) -> float:
    """
    Calculate confidence score (0.0 to 1.0) for the generated response.
    Combines vector retrieval similarity scores with citation matching statistics.
    """
    if not retrieved_nodes:
        return 0.0

    # 1. Average similarity score of top retrieval nodes
    avg_retrieval_score = sum(node.score or 0.0 for node in retrieved_nodes) / len(
        retrieved_nodes
    )

    # Normalize score (sometimes Cosine or Dot Product is above/below 0-1 depending on model)
    avg_retrieval_score = max(0.0, min(1.0, avg_retrieval_score))

    # 2. Check overlap between response and source citations (token match heuristic)
    # Simple check: what fraction of key terms in the response appear in retrieved nodes
    response_words = set(response_text.lower().split())
    # filter short stop words
    response_words = {w for w in response_words if len(w) > 4}

    if not response_words:
        return round(avg_retrieval_score, 2)

    context_text = " ".join(
        [node.node.get_content().lower() for node in retrieved_nodes]
    )
    matched_words = sum(1 for w in response_words if w in context_text)
    overlap_ratio = matched_words / len(response_words)

    # Fuse scores (70% retrieval relevance, 30% lexical overlap)
    final_score = (avg_retrieval_score * 0.7) + (overlap_ratio * 0.3)

    return round(max(0.0, min(1.0, final_score)), 2)
