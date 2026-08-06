"""
PakLaw AI — Celery App Instance Configuration
"""

import sys
from pathlib import Path

# Add project root to sys.path so workers can find backend and ai modules
sys.path.append(str(Path(__file__).parent.parent))

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "paklawai_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery Configurations
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Karachi",
    enable_utc=True,
    # Configure task routing queue parameters
    task_routes={
        "workers.tasks.ingestion.process_document_task": {"queue": "ingestion"},
        "workers.tasks.ingestion.delete_document_vector_task": {"queue": "ingestion"},
        "workers.tasks.report.generate_research_report_task": {"queue": "ai"},
    },
    # Retry connecting to broker on startup
    broker_connection_retry_on_startup=True,
)

# Autodiscover background tasks modules
celery_app.autodiscover_tasks(
    [
        "workers.tasks.ingestion",
        "workers.tasks.report",
    ]
)
