from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


celery_app = Celery(
    "bookstore",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True

import app.tasks.discount_tasks

celery_app.conf.beat_schedule = {
    "deactivate-expired-discounts-every-minute": {
        "task": "deactivate_expired_discounts",
        "schedule": crontab(minute="*"),
    },
}