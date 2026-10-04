"""
celery_app.py
─────────────
Celery application instance for FlowGuard AI background tasks.

The worker is started with:
    celery -A celery_app worker --loglevel=info

Broker (Redis) URL is read from the REDIS_URL environment variable,
falling back to localhost for local development.
"""
import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "flowguard",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Allow the worker to import tasks from the ai/ package
    include=["ai.tasks"],
    # Task result expiry (7 days)
    result_expires=60 * 60 * 24 * 7,
)
