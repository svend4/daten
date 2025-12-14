"""
Celery application for background tasks
"""

from celery import Celery
from ios_core.config import settings

# Create Celery app
celery_app = Celery(
    'ios_tasks',
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
    include=['ios_core.tasks.document_tasks', 'ios_core.tasks.maintenance_tasks']
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Task routes
celery_app.conf.task_routes = {
    'ios_core.tasks.document_tasks.*': {'queue': 'documents'},
    'ios_core.tasks.maintenance_tasks.*': {'queue': 'maintenance'},
}