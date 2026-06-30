from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

import app.tasks.discount_tasks
import app.tasks.parser_tasks


celery_app = Celery(
    "bookstore",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "deactivate-expired-discounts-every-minute": {
            "task": "deactivate_expired_discounts",
            "schedule": crontab(minute="*"),
        },
    },
)