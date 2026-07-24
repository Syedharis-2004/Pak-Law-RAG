"""
PakLaw AI Backend — Async MongoDB Engine & Client Manager

Provides motor AsyncIOMotorClient connection pooling,
database access, index creation for collections, and ping diagnostics.
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("mongodb")

class MongoDBManager:
    """Manages async MongoDB client connection pool and database access."""

    def __init__(self) -> None:
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    def get_client(self) -> AsyncIOMotorClient:
        if self.client is None:
            logger.info("Initializing MongoDB client", url=settings.MONGODB_URL)
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
            )
        return self.client

    def get_database(self) -> AsyncIOMotorDatabase:
        if self.db is None:
            client = self.get_client()
            self.db = client[settings.MONGODB_DB_NAME]
        return self.db

    async def init_indexes(self) -> None:
        """Create indexes on MongoDB collections for optimal query performance."""
        try:
            db = self.get_database()
            # Documents collection indexes
            await db.documents.create_index("id", unique=True)
            await db.documents.create_index("slug", unique=True)
            await db.documents.create_index("checksum_sha256")
            await db.documents.create_index("document_type")
            await db.documents.create_index("status")

            # Chunks collection indexes
            await db.chunks.create_index("id", unique=True)
            await db.chunks.create_index("document_id")
            await db.chunks.create_index("chunk_index")
            await db.chunks.create_index("qdrant_point_id")

            # Users collection indexes
            await db.users.create_index("id", unique=True)
            await db.users.create_index("email", unique=True)

            # Processing jobs collection indexes
            await db.processing_jobs.create_index("id", unique=True)
            await db.processing_jobs.create_index("document_id")

            # Chats / Search logs indexes
            await db.chats.create_index("id", unique=True)
            await db.chats.create_index("user_id")
            await db.search_logs.create_index("id", unique=True)

            logger.info("MongoDB indexes created successfully", db_name=settings.MONGODB_DB_NAME)
        except Exception as e:
            logger.warning("MongoDB index initialization warning", error=str(e))

    async def ping(self) -> bool:
        """Check if MongoDB instance is alive and reachable."""
        try:
            client = self.get_client()
            await client.admin.command("ping")
            return True
        except Exception as e:
            logger.debug("MongoDB ping failed", error=str(e))
            return False

    def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

mongodb_manager = MongoDBManager()

async def get_mongodb() -> AsyncIOMotorDatabase:
    """Dependency helper to return active MongoDB database."""
    return mongodb_manager.get_database()
