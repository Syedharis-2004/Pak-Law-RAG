"""
PakLaw AI — Advanced Search Router

Supports hybrid semantic search + dense/sparse keyword lookup.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user, get_user_repository
from app.repositories.document import DocumentRepository
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search import SearchService

router = APIRouter(prefix="/search", tags=["Search Engine"])


async def get_document_repository(db=Depends(get_user_repository)) -> DocumentRepository:
    from app.models.document import Document

    return DocumentRepository(Document, db.db)


async def get_search_service(
    repo: Annotated[DocumentRepository, Depends(get_document_repository)],
) -> SearchService:
    return SearchService(repo)


@router.post("", response_model=SearchResponse)
async def advanced_search(
    request: SearchRequest,
    current_user: Annotated[object, Depends(get_current_user)],
    search_service: Annotated[SearchService, Depends(get_search_service)],
):
    """
    Search legal acts, regulations, ordinances, and court judgments.
    Supports dense vectors, sparse keyword indices, and filters.
    """
    return await search_service.execute_search(request)
