"""
PakLaw AI — Qdrant Collections Manager

Handles creating, dropping, and configuring collection schemas
for dense, sparse, and payload metadata fields.
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("qdrant")


class QdrantCollectionManager:
    """Manages Qdrant vector database collections and indexes."""

    def __init__(self) -> None:
        import socket

        qdrant_online = False
        try:
            with socket.create_connection(
                (settings.QDRANT_HOST, settings.QDRANT_PORT), timeout=0.5
            ):
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
                self.client = client
            except Exception:
                self.client = QdrantClient(path="./qdrant_db")
        else:
            self.client = QdrantClient(path="./qdrant_db")

    def init_collections(self) -> None:
        """Initialize all required vector collections with schemas."""
        collections_to_create = [
            "legal_documents",
        ]

        for collection in collections_to_create:
            self.create_collection_if_not_exists(collection)

    def create_collection_if_not_exists(self, collection_name: str) -> None:
        """Create a collection supporting hybrid (Dense + Sparse) search capabilities."""
        try:
            # Check if collection exists
            self.client.get_collection(collection_name)
            logger.info("Collection already exists", collection=collection_name)
        except (UnexpectedResponse, Exception):
            # Create collection
            logger.info("Creating Qdrant collection", collection=collection_name)

            # Configure collection options
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=settings.EMBEDDING_DIMENSION,  # 1024 for BGE-M3
                    distance=models.Distance.COSINE,
                ),
                # Setup Sparse vector config for BM25 keyword matching
                sparse_vectors_config={
                    "sparse-text": models.SparseVectorParams(
                        index=models.SparseIndexParams(
                            on_disk=True,
                        )
                    )
                },
            )

            # Create payload indexes for metadata filtering
            self.create_payload_indexes(collection_name)

    def create_payload_indexes(self, collection_name: str) -> None:
        """Create indexes on payload fields to optimize filtering."""
        fields_to_index = [
            ("document_id", models.PayloadSchemaType.KEYWORD),
            ("document_type", models.PayloadSchemaType.KEYWORD),
            ("jurisdiction", models.PayloadSchemaType.KEYWORD),
            ("year", models.PayloadSchemaType.INTEGER),
            ("language", models.PayloadSchemaType.KEYWORD),
        ]

        for field_name, schema_type in fields_to_index:
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema_type,
            )

        logger.info("Payload indexes initialized", collection=collection_name)

    def drop_collection(self, collection_name: str) -> None:
        """Drop a collection completely."""
        try:
            self.client.delete_collection(collection_name)
            logger.info("Dropped collection", collection=collection_name)
        except Exception as e:
            logger.error(
                "Failed to drop collection", collection=collection_name, error=str(e)
            )
