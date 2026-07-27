"""
PakLaw AI — Hybrid Dense + Sparse Retrieval Pipeline

Runs vector searches matching semantic constructs, sparse lexical searches (BM25),
fuses scores, applies metadata filters, and filters results using BGE Cross-Encoder.
"""

from typing import Any, Dict, List

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
try:
    from llama_index.core.schema import NodeWithScore, TextNode
except Exception:
    class TextNode:
        def __init__(self, text="", id_="", metadata=None):
            self.text = text
            self.id_ = id_
            self.metadata = metadata or {}
        def get_content(self):
            return self.text
    class NodeWithScore:
        def __init__(self, node=None, score=0.0):
            self.node = node
            self.score = score

from app.core.config import settings
from ai.embeddings.bge_m3 import BGEM3Embedding
from ai.reranker.bge_reranker import BGEReranker


class HybridRetriever:
    """Executes dense + sparse search queries on Qdrant and reranks matches."""

    def __init__(self) -> None:
        import socket
        qdrant_online = False
        try:
            with socket.create_connection((settings.QDRANT_HOST, settings.QDRANT_PORT), timeout=0.5):
                qdrant_online = True
        except Exception:
            qdrant_online = False

        if qdrant_online:
            try:
                client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY,
                    https=settings.QDRANT_HTTPS,
                    timeout=2.0,
                )
                client.get_collections()
                self.qdrant_client = client
            except Exception:
                self.qdrant_client = QdrantClient(path="./qdrant_db")
        else:
            self.qdrant_client = QdrantClient(path="./qdrant_db")
        self.embed_model = BGEM3Embedding()
        self.reranker = BGEReranker()

    def _do_search(self, collection_name: str, query_vector: Any, query_filter: Any, limit: int) -> List[Any]:
        """Supports both QdrantClient.query_points (v1.18+) and legacy .search()."""
        try:
            if hasattr(self.qdrant_client, "query_points"):
                if isinstance(query_vector, qdrant_models.NamedSparseVector):
                    res = self.qdrant_client.query_points(
                        collection_name=collection_name,
                        query=query_vector.vector,
                        using="sparse-text",
                        query_filter=query_filter,
                        limit=limit,
                    )
                else:
                    res = self.qdrant_client.query_points(
                        collection_name=collection_name,
                        query=query_vector,
                        query_filter=query_filter,
                        limit=limit,
                    )
                return getattr(res, "points", res)
            elif hasattr(self.qdrant_client, "search"):
                return self.qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                )
        except Exception as e:
            import logging
            logging.warning(f"Qdrant search error: {e}")
        return []

    async def retrieve(
        self,
        query: str,
        filters: Dict[str, Any] | None = None,
        top_k: int = 20,
        search_type: str = "hybrid",
    ) -> List[NodeWithScore]:
        """
        Retrieves matching document chunks from Qdrant.
        Fuses dense + sparse searches, applies filters, and runs BGE Cross-Encoder reranker.
        """
        # Determine target collection based on document type query, fallback to generic
        collection_name = "legal_documents"
        
        # Build Qdrant filter object
        qdrant_filter = self._build_qdrant_filter(filters)

        dense_results = []
        sparse_results = []

        # ── 1. Dense Semantic Search ──────────────────────────────
        if search_type in ("semantic", "hybrid"):
            query_vector = self.embed_model.get_query_embedding(query)
            dense_hits = self._do_search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
            )
            dense_results = self._hits_to_nodes(dense_hits)

        # ── 2. Sparse Keyword Search ──────────────────────────────
        if search_type in ("keyword", "hybrid"):
            sparse_vector = self.embed_model.get_sparse_embedding(query)
            indices = list(sparse_vector.keys())
            values = list(sparse_vector.values())

            sparse_hits = self._do_search(
                collection_name=collection_name,
                query_vector=qdrant_models.NamedSparseVector(
                    name="sparse-text",
                    vector=qdrant_models.SparseVector(
                        indices=indices,
                        values=values
                    )
                ),
                query_filter=qdrant_filter,
                limit=top_k,
            )
            sparse_results = self._hits_to_nodes(sparse_hits)

        # ── 3. Dense/Sparse Fusion ────────────────────────────────
        fused_nodes = self._fuse_results(dense_results, sparse_results, alpha=settings.HYBRID_SEARCH_ALPHA)

        # ── 4. Cross-Encoder Reranking ────────────────────────────
        try:
            from llama_index.core.schema import QueryBundle
            query_bundle = QueryBundle(query_str=query)
        except Exception:
            from ai.reranker.bge_reranker import QueryBundle
            query_bundle = QueryBundle(query_str=query)
        
        reranked_nodes = self.reranker._postprocess_nodes(
            nodes=fused_nodes,
            query_bundle=query_bundle
        )

        return reranked_nodes

    def _build_qdrant_filter(self, filters: Dict[str, Any] | None) -> qdrant_models.Filter | None:
        """Convert basic filter dict to Qdrant Filter conditions."""
        if not filters:
            return None

        must_conditions = []
        for key, value in filters.items():
            if not value:
                continue
            
            if isinstance(value, list):
                # Multiple match condition (OR within the field)
                must_conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchAny(any=value)
                    )
                )
            else:
                must_conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchValue(value=value)
                    )
                )

        if not must_conditions:
            return None
            
        return qdrant_models.Filter(must=must_conditions)

    def _hits_to_nodes(self, hits: List[Any]) -> List[NodeWithScore]:
        """Convert Qdrant Search hits to LlamaIndex NodeWithScore format."""
        nodes = []
        for hit in hits:
            node = TextNode(
                text=hit.payload.get("text", ""),
                id_=hit.id,
                metadata=hit.payload,
            )
            nodes.append(NodeWithScore(node=node, score=hit.score))
        return nodes

    def _fuse_results(
        self,
        dense_nodes: List[NodeWithScore],
        sparse_nodes: List[NodeWithScore],
        alpha: float = 0.7
    ) -> List[NodeWithScore]:
        """Combines dense and sparse scores (Reciprocal Rank Fusion heuristic or raw score addition)."""
        # Dictionary mapping point_id -> NodeWithScore
        fused_dict = {}

        # 1. Add dense scores
        for node in dense_nodes:
            fused_dict[node.node.id_] = {
                "node": node.node,
                "score": (node.score or 0.0) * alpha
            }

        # 2. Add sparse scores
        for node in sparse_nodes:
            point_id = node.node.id_
            sparse_weighted = (node.score or 0.0) * (1.0 - alpha)
            if point_id in fused_dict:
                fused_dict[point_id]["score"] += sparse_weighted
            else:
                fused_dict[point_id] = {
                    "node": node.node,
                    "score": sparse_weighted
                }

        # Convert back to NodeWithScore objects
        results = []
        for point_id, data in fused_dict.items():
            results.append(NodeWithScore(node=data["node"], score=data["score"]))

        # Sort by fused score descending
        return sorted(results, key=lambda x: x.score or 0.0, reverse=True)
