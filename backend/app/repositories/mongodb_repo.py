"""
PakLaw AI Backend — MongoDB Repository & Dual Sync Helper

Handles storing and retrieving documents, chunks, users, jobs, and search logs
in MongoDB collections so MongoDB Compass can be used to inspect all system data.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.mongodb import mongodb_manager
from app.core.logging_config import get_logger

logger = get_logger("mongodb_repo")


def _sanitize_for_mongo(obj: Any) -> Any:
    """Recursively convert UUIDs, datetimes, and Enums for BSON compatibility in MongoDB."""
    if obj is None:
        return None
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "value"):
        return obj.value
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_mongo(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_mongo(item) for item in obj]
    return obj


class MongoDBRepository:
    """Repository helper to sync relational entity records into MongoDB collections."""

    @staticmethod
    async def sync_document(doc_dict: Dict[str, Any]) -> None:
        """Upsert document metadata into MongoDB 'documents' collection."""
        if not settings.USE_MONGODB:
            return
        try:
            db = mongodb_manager.get_database()
            data = _sanitize_for_mongo(doc_dict)
            doc_id = data.get("id")
            if not doc_id:
                return

            # Keep _id friendly for MongoDB Compass
            data["_id"] = doc_id
            data["updated_at_mongo"] = datetime.now(timezone.utc).isoformat()

            await db.documents.update_one(
                {"id": doc_id},
                {"$set": data},
                upsert=True
            )
            logger.debug("Synced document to MongoDB", document_id=doc_id)
        except Exception as e:
            logger.warning("Failed to sync document to MongoDB", error=str(e))

    @staticmethod
    async def sync_chunk(chunk_dict: Dict[str, Any]) -> None:
        """Upsert document chunk into MongoDB 'chunks' collection."""
        if not settings.USE_MONGODB:
            return
        try:
            db = mongodb_manager.get_database()
            data = _sanitize_for_mongo(chunk_dict)
            chunk_id = data.get("id")
            if not chunk_id:
                return

            data["_id"] = chunk_id
            await db.chunks.update_one(
                {"id": chunk_id},
                {"$set": data},
                upsert=True
            )
            logger.debug("Synced chunk to MongoDB", chunk_id=chunk_id)
        except Exception as e:
            logger.warning("Failed to sync chunk to MongoDB", error=str(e))

    @staticmethod
    async def sync_user(user_dict: Dict[str, Any]) -> None:
        """Upsert user profile into MongoDB 'users' collection."""
        if not settings.USE_MONGODB:
            return
        try:
            db = mongodb_manager.get_database()
            data = _sanitize_for_mongo(user_dict)
            user_id = data.get("id")
            if not user_id:
                return

            data["_id"] = user_id
            await db.users.update_one(
                {"id": user_id},
                {"$set": data},
                upsert=True
            )
            logger.debug("Synced user to MongoDB", user_id=user_id)
        except Exception as e:
            logger.warning("Failed to sync user to MongoDB", error=str(e))

    @staticmethod
    async def sync_job(job_dict: Dict[str, Any]) -> None:
        """Upsert processing job record into MongoDB 'processing_jobs' collection."""
        if not settings.USE_MONGODB:
            return
        try:
            db = mongodb_manager.get_database()
            data = _sanitize_for_mongo(job_dict)
            job_id = data.get("id")
            if not job_id:
                return

            data["_id"] = job_id
            await db.processing_jobs.update_one(
                {"id": job_id},
                {"$set": data},
                upsert=True
            )
            logger.debug("Synced processing job to MongoDB", job_id=job_id)
        except Exception as e:
            logger.warning("Failed to sync job to MongoDB", error=str(e))

    @staticmethod
    async def sync_search_log(log_dict: Dict[str, Any]) -> None:
        """Insert search/query log into MongoDB 'search_logs' collection."""
        if not settings.USE_MONGODB:
            return
        try:
            db = mongodb_manager.get_database()
            data = _sanitize_for_mongo(log_dict)
            log_id = data.get("id", str(uuid.uuid4()))
            data["_id"] = log_id
            await db.search_logs.update_one(
                {"id": log_id},
                {"$set": data},
                upsert=True
            )
        except Exception as e:
            logger.warning("Failed to sync search log to MongoDB", error=str(e))

    @staticmethod
    async def get_documents(limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch documents stored in MongoDB collection."""
        try:
            db = mongodb_manager.get_database()
            cursor = db.documents.find({}).limit(limit)
            return [doc async for doc in cursor]
        except Exception as e:
            logger.error("Failed to query MongoDB documents", error=str(e))
            return []

    @staticmethod
    async def get_chunks_by_document(document_id: str) -> List[Dict[str, Any]]:
        """Fetch all chunks for a document from MongoDB collection."""
        try:
            db = mongodb_manager.get_database()
            cursor = db.chunks.find({"document_id": str(document_id)}).sort("chunk_index", 1)
            return [chunk async for chunk in cursor]
        except Exception as e:
            logger.error("Failed to query MongoDB chunks", error=str(e))
            return []
