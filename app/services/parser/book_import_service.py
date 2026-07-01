import logging
from datetime import UTC, datetime

from app.db.collections import get_category_collection, get_product_collection
from app.services.parser.books_to_scrape_service import get_full_book_by_url, get_full_books_from_category
from app.services.parser.parser_mapper import map_scraped_book_to_product
from app.services.product_service import create_product

logger = logging.getLogger(__name__)


async def get_or_create_category(category_name: str) -> str:
    category_collection = get_category_collection()

    category = await category_collection.find_one(
        {
            "name": category_name,
            "is_active": True,
        }
    )

    if category:
        logger.info("Category already exists: %s", category_name)
        return str(category["_id"])

    now = datetime.now(UTC)

    result = await category_collection.insert_one(
        {
            "name": category_name,
            "slug": category_name.lower().replace(" ", "-"),
            "description": "Automatically imported category from BooksToScrape.",
            "category_type": "book",
            "parent_id": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    )

    logger.info("Category created: %s", category_name)
    return str(result.inserted_id)


async def product_exists(upc: str | None) -> bool:
    if not upc:
        return False

    product_collection = get_product_collection()

    product = await product_collection.find_one(
        {
            "book_details.upc": upc,
        }
    )

    return product is not None


async def import_single_scraped_book(
    scraped_book: dict,
    category_id: str,
):
    upc = scraped_book.get("upc")

    if await product_exists(upc):
        return None, "skipped"

    product_data = map_scraped_book_to_product(
        scraped_book=scraped_book,
        category_id=category_id,
    )

    created_product = await create_product(product_data)

    return created_product, "created"


async def import_books_from_category(
    category_name: str,
    category_url: str,
    limit: int | None = None,
):
    logger.info(
        "Category import started. Category=%s, limit=%s",
        category_name,
        limit,
    )

    category_id = await get_or_create_category(category_name)

    scraped_books = await get_full_books_from_category(
        category_url=category_url,
        limit=limit,
    )

    created_products = []
    created_count = 0
    skipped_count = 0
    failed_count = 0
    errors = []

    for scraped_book in scraped_books:
        try:
            created_product, status = await import_single_scraped_book(
                scraped_book=scraped_book,
                category_id=category_id,
            )

            if status == "skipped":
                skipped_count += 1
                continue

            created_products.append(created_product)
            created_count += 1

        except Exception as exc:
            failed_count += 1
            book_name = scraped_book.get("name", "Unknown book")

            logger.exception("Failed to import book: %s", book_name)

            errors.append(
                {
                    "book": book_name,
                    "error": str(exc),
                }
            )

    logger.info(
        "Category import finished. Category=%s, created=%s, skipped=%s, failed=%s, total=%s",
        category_name,
        created_count,
        skipped_count,
        failed_count,
        len(scraped_books),
    )

    return {
        "category": category_name,
        "created_count": created_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "total_parsed": len(scraped_books),
        "errors": errors,
        "products": created_products,
    }


async def import_custom_books(books: list[dict]):
    logger.info("Custom import started. Count=%s", len(books))

    created_products = []
    created_count = 0
    skipped_count = 0
    failed_count = 0
    errors = []

    for book_item in books:
        category_name = book_item.get("category_name")
        book_url = book_item.get("book_url")

        try:
            category_id = await get_or_create_category(category_name)
            scraped_book = await get_full_book_by_url(book_url)

            created_product, status = await import_single_scraped_book(
                scraped_book=scraped_book,
                category_id=category_id,
            )

            if status == "skipped":
                skipped_count += 1
                continue

            created_products.append(created_product)
            created_count += 1

        except Exception as exc:
            failed_count += 1

            logger.exception(
                "Failed to import custom book: category=%s, url=%s",
                category_name,
                book_url,
            )

            errors.append(
                {
                    "category": category_name,
                    "book_url": book_url,
                    "error": str(exc),
                }
            )

    logger.info(
        "Custom import finished. Created=%s, skipped=%s, failed=%s, total=%s",
        created_count,
        skipped_count,
        failed_count,
        len(books),
    )

    return {
        "created_count": created_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "total_requested": len(books),
        "errors": errors,
        "products": created_products,
    }