import asyncio

from app.core.celery_app import celery_app
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.services.discount_service import deactivate_expired_discounts


@celery_app.task(name="deactivate_expired_discounts")
def deactivate_expired_discounts_task():
    async def run():
        await connect_to_mongo()

        try:
            return await deactivate_expired_discounts()
        finally:
            await close_mongo_connection()

    return asyncio.run(run())