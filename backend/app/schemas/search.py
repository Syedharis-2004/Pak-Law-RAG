"""
PakLaw AI — Search Pydantic Schemas
"""

import uuid
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    search_type: str = Field("hybrid", pattern="^(semantic|keyword|hybrid|metadata)$")
    document_types: list[str] | None = None
    jurisdictions: list[str] | None = None
    years: list[int] | None = None
    languages: list[str] | None = None
    document_ids: list[uuid.UUID] | None = None
    top_k: int = Field(10, ge=1, le=50)
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=50)


class SearchResultItem(BaseModel):
    document_id: uuid.UUID
    chunk_id: uuid.UUID
    document_title: str
    document_type: str
    jurisdiction: str | None
    year: int | None
    section_number: str | None
    section_title: str | None
    content: str
    page_number: int | None
    score: float
    search_type: str
    highlight: str | None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    total: int
    page: int
    page_size: int
    search_time_ms: float
    language_detected: str


class SuggestRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(5, ge=1, le=20)


class SuggestResponse(BaseModel):
    suggestions: list[str]
