"""
PakLaw AI — Advanced Legal Search Service

Implements dense semantic search, sparse BM25 keyword search, metadata filtering,
and cross-encoder reranking.
"""

import time
import uuid

from app.core.exceptions import RetrievalError
from app.repositories.document import DocumentRepository
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem


class SearchService:
    """Service layer for hybrid Dense + Sparse search with reranking."""

    def __init__(self, doc_repo: DocumentRepository) -> None:
        self.doc_repo = doc_repo

    async def execute_search(self, request: SearchRequest) -> SearchResponse:
        """
        Run hybrid search across Qdrant vector database, perform dense/sparse fusion,
        apply metadata filtering, rerank with BGE Cross-Encoder, and return results.
        """
        start_time = time.perf_counter()

        # Detect query language
        from ai.utils.language_detection import detect_language
        lang = detect_language(request.query)

        # 1. Initialize Hybrid Retrieval pipeline
        from ai.pipelines.retrieval import HybridRetriever
        retriever = HybridRetriever()

        # Formulate filters
        filters = {}
        if request.document_types:
            filters["document_type"] = request.document_types
        if request.jurisdictions:
            filters["jurisdiction"] = request.jurisdictions
        if request.years:
            filters["year"] = request.years
        if request.languages:
            filters["language"] = request.languages
        if request.document_ids:
            filters["document_id"] = [str(d) for d in request.document_ids]

        # 2. Retrieve matched chunks
        try:
            retrieved_nodes = await retriever.retrieve(
                query=request.query,
                filters=filters,
                top_k=request.top_k,
                search_type=request.search_type,
            )
        except Exception as e:
            raise RetrievalError(f"Error during vector/keyword search: {str(e)}")

        # 3. Formulate SearchResultItems
        results = []
        for node in retrieved_nodes:
            meta = node.metadata
            doc_id = uuid.UUID(meta.get("document_id")) if meta.get("document_id") else uuid.uuid4()
            chunk_id = uuid.UUID(meta.get("chunk_id")) if meta.get("chunk_id") else uuid.uuid4()

            results.append(
                SearchResultItem(
                    document_id=doc_id,
                    chunk_id=chunk_id,
                    document_title=meta.get("title", "Official Legal Document"),
                    document_type=meta.get("document_type", "other"),
                    jurisdiction=meta.get("jurisdiction"),
                    year=meta.get("year"),
                    section_number=meta.get("section_number"),
                    section_title=meta.get("section_title"),
                    content=node.text,
                    page_number=meta.get("page_number"),
                    score=float(node.score or 0.0),
                    search_type=request.search_type,
                    highlight=None,  # Optional highlight snippet
                )
            )

        # Pagination slicing (since reranking operates on top_k retrieve pool)
        total = len(results)
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        paginated_results = results[start_idx:end_idx]

        end_time = time.perf_counter()
        search_time_ms = (end_time - start_time) * 1000

        return SearchResponse(
            query=request.query,
            results=paginated_results,
            total=total,
            page=request.page,
            page_size=request.page_size,
            search_time_ms=search_time_ms,
            language_detected=lang,
        )
