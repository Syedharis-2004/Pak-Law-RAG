"""
PakLaw AI — Ingestion Celery Tasks

Handles asynchronous document processing (ingestion and deletions).
"""

import asyncio

from celery.utils.log import get_task_logger

from ai.pipelines.ingestion import IngestionPipeline
from workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(
    name="workers.tasks.ingestion.process_document_task", bind=True, max_retries=3
)
def process_document_task(self, document_id: str, job_id: str) -> str:
    """
    Background worker task invoking the ingestion pipeline.
    Runs asynchronously on file uploads.
    """
    logger.info(
        f"Starting document ingestion. Document ID: {document_id}, Job ID: {job_id}"
    )

    pipeline = IngestionPipeline()

    # Create event loop for execution since FastAPI pipeline utilizes async dependencies
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(pipeline.ingest_document(document_id, job_id))
        logger.info(
            f"Document ingestion completed successfully for Document ID: {document_id}"
        )
        return "SUCCESS"
    except Exception as e:
        logger.error(f"Ingestion failed for Document ID: {document_id}. Error: {e!s}")
        # Automatic retry logic
        try:
            self.retry(exc=e, countdown=60)
        except Exception:
            return "FAILED"


@celery_app.task(name="workers.tasks.ingestion.delete_document_vector_task")
def delete_document_vector_task(document_id: str) -> str:
    """
    Prunes points belonging to a soft-deleted document from Qdrant vector store.
    """
    logger.info(f"Deleting vector indexing points for Document ID: {document_id}")

    from qdrant_client.http import models as qdrant_models

    from ai.qdrant.collections import QdrantCollectionManager

    manager = QdrantCollectionManager()
    collections = [
        "acts",
        "ordinances",
        "rules",
        "judgments",
        "contracts",
        "legal_documents",
    ]

    # Delete match filters from all collections
    for collection in collections:
        try:
            manager.client.delete(
                collection_name=collection,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="document_id",
                                match=qdrant_models.MatchValue(value=document_id),
                            )
                        ]
                    )
                ),
            )
        except Exception as e:
            logger.warning(
                f"Failed deleting points from collection '{collection}': {e!s}"
            )

    logger.info(f"Vector deletion complete for Document ID: {document_id}")
    return "SUCCESS"
