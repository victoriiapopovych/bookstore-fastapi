import asyncio

from celery import shared_task

from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.services.parser.book_import_service import import_books_from_category, import_custom_books


@shared_task(name="import_books_from_category")
def import_books_from_category_task(category_name: str, category_url: str, limit: int | None = None):
    async def run():
        await connect_to_mongo()

        try:
            return await import_books_from_category(
                category_name=category_name,
                category_url=category_url,
                limit=limit,
            )
        finally:
            await close_mongo_connection()

    return asyncio.run(run())


@shared_task(name="import_custom_books")
def import_custom_books_task(books: list[dict]):
    async def run():
        await connect_to_mongo()

        try:
            return await import_custom_books(books)
        finally:
            await close_mongo_connection()

    return asyncio.run(run())