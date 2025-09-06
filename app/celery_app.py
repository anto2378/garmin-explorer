"""
Celery configuration for background tasks
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery instance
celery = Celery(
    "garmin_companion",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Configure Celery
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Scheduled tasks
celery.conf.beat_schedule = {
    # Sync all users' activities daily at 6 AM
    "daily-activity-sync": {
        "task": "app.tasks.sync_all_users_activities",
        "schedule": crontab(hour=6, minute=0),
    },
    
    # Generate weekly digests on Mondays at 8 AM
    "weekly-digest-generation": {
        "task": "app.tasks.generate_weekly_digests",
        "schedule": crontab(day_of_week=1, hour=8, minute=0),
    },
    
    # Cleanup old data monthly
    "monthly-cleanup": {
        "task": "app.tasks.cleanup_old_data",
        "schedule": crontab(day_of_month=1, hour=2, minute=0),
    },
}

celery.conf.timezone = "UTC"