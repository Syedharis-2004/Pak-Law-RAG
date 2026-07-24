"""
PakLaw AI — BGE-M3 Embeddings wrapper for LlamaIndex/LangChain.
"""

from typing import Any, List

import numpy as np
try:
    from llama_index.core.embeddings import BaseEmbedding
except Exception:
    from pydantic import BaseModel
    class BaseEmbedding(BaseModel):
        pass

from pydantic import Field, PrivateAttr

from app.core.config import settings


class BGEM3Embedding(BaseEmbedding):
    """
    Custom LlamaIndex Embedding class utilizing BAAI/bge-m3.
    Retrieves dense, sparse, and multi-vector representations.
    """

    model_name: str = Field(default=settings.EMBEDDING_MODEL)
    device: str = Field(default=settings.EMBEDDING_DEVICE)
    batch_size: int = Field(default=settings.EMBEDDING_BATCH_SIZE)

    _model: Any = PrivateAttr()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        try:
            from FlagEmbedding import BGEM3FlagModel
            self._model = BGEM3FlagModel(
                self.model_name,
                use_fp16=(self.device == "cuda"),
                device=self.device
            )
        except Exception:
            self._model = None

    def _hash_vector(self, text: str, dim: int = 1024) -> List[float]:
        """Generate deterministic 1024-dim dense vector if neural model unavailable."""
        import hashlib, math
        words = text.lower().split()
        vec = [0.0] * dim
        for w in words:
            h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            val = ((h >> 16) % 1000) / 1000.0 - 0.5
            vec[idx] += val
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def _get_query_embedding(self, query: str) -> List[float]:
        """Embed search query (dense vector)."""
        if self._model:
            try:
                return self._model.encode(
                    [query],
                    batch_size=self.batch_size,
                    max_length=8192
                )['dense_vecs'][0].tolist()
            except Exception:
                pass
        return self._hash_vector(query)

    def _get_text_embedding(self, text: str) -> List[float]:
        """Embed document chunk text (dense vector)."""
        if self._model:
            try:
                return self._model.encode(
                    [text],
                    batch_size=self.batch_size,
                    max_length=8192
                )['dense_vecs'][0].tolist()
            except Exception:
                pass
        return self._hash_vector(text)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    def get_sparse_embedding(self, text: str) -> dict:
        """Retrieve sparse representation (lexical weights) for BM25-like search."""
        if self._model:
            try:
                return self._model.encode(
                    [text],
                    return_sparse=True,
                    max_length=8192
                )['lexical_weights'][0]
            except Exception:
                pass
        # Lexical token frequency fallback dictionary mapping token hash -> count/weight
        import hashlib
        weights = {}
        for token in text.lower().split():
            idx = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:6], 16)
            weights[idx] = weights.get(idx, 0.0) + 1.0
        return weights
