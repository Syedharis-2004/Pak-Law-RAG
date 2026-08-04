"""
PakLaw AI — BGE Cross-Encoder Reranker

Reranks retrieved document chunks using BAAI/bge-reranker-v2-m3.
"""

from typing import Any

try:
    from llama_index.core.postprocessor.types import BaseNodePostprocessor
    from llama_index.core.schema import NodeWithScore, QueryBundle
except Exception:
    from pydantic import BaseModel

    class BaseNodePostprocessor(BaseModel):
        pass

    class NodeWithScore:
        def __init__(self, node=None, score=0.0):
            self.node = node
            self.score = score

    class QueryBundle:
        def __init__(self, query_str=""):
            self.query_str = query_str


from app.core.config import settings
from pydantic import Field, PrivateAttr


class BGEReranker(BaseNodePostprocessor):
    """
    Reranks retrieved candidate nodes using a local Cross-Encoder model
    to increase precision and filter noise.
    """

    model_name: str = Field(default=settings.RERANKER_MODEL)
    device: str = Field(default=settings.RERANKER_DEVICE)
    top_n: int = Field(default=settings.RERANKER_FINAL_TOP_K)

    _reranker: Any = PrivateAttr()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._reranker = None
        if self.device == "cuda":
            try:
                from FlagEmbedding import FlagReranker

                self._reranker = FlagReranker(
                    self.model_name, use_fp16=True, device=self.device
                )
            except Exception:
                self._reranker = None

    @classmethod
    def class_name(cls) -> str:
        return "BGEReranker"

    def _postprocess_nodes(
        self,
        nodes: list[NodeWithScore],
        query_bundle: QueryBundle = None,
    ) -> list[NodeWithScore]:
        if not nodes or not query_bundle:
            return nodes

        query = query_bundle.query_str

        if self._reranker:
            try:
                pairs = [[query, node.node.get_content()] for node in nodes]
                scores = self._reranker.compute_score(pairs)
                if isinstance(scores, (float, int)):
                    scores = [scores]
                for idx, score in enumerate(scores):
                    nodes[idx].score = float(score)
                sorted_nodes = sorted(nodes, key=lambda x: x.score or 0.0, reverse=True)
                return sorted_nodes[: self.top_n]
            except Exception:
                pass

        # Fallback scoring: Lexical keyword overlap
        query_words = set(query.lower().split())
        for node in nodes:
            content_words = node.node.get_content().lower().split()
            overlap = sum(1 for w in content_words if w in query_words)
            node.score = (node.score or 0.0) + (overlap * 0.1)

        sorted_nodes = sorted(nodes, key=lambda x: x.score or 0.0, reverse=True)
        return sorted_nodes[: self.top_n]
