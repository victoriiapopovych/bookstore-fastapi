from fastapi import APIRouter, Depends

from app.core.celery_app import celery_app
from app.dependencies.auth import require_manager
from app.schemas.parser import ImportCategoryRequest, ImportCustomBooksRequest
from app.services.parser.books_to_scrape_service import get_available_categories, get_book_details, get_books_from_category, get_full_books_from_category

from app.utils.pagination import PaginationParams, build_paginated_response


router = APIRouter(prefix="/parser", tags=["Parser"])


@router.get("/categories", dependencies=[Depends(require_manager)])
async def get_categories_endpoint(
    pagination: PaginationParams = Depends(),
):
    categories = await get_available_categories()

    start = (pagination.page - 1) * pagination.page_size
    end = start + pagination.page_size

    return build_paginated_response(
        items=categories[start:end],
        total=len(categories),
        params=pagination,
    )


@router.get("/category/books", dependencies=[Depends(require_manager)])
async def get_books_from_category_endpoint(
    category_url: str,
    limit: int | None = None,
    pagination: PaginationParams = Depends(),
):
    books = await get_books_from_category(
        category_url=category_url,
        limit=limit,
    )

    start = (pagination.page - 1) * pagination.page_size
    end = start + pagination.page_size

    return build_paginated_response(
        items=books[start:end],
        total=len(books),
        params=pagination,
    )


@router.get("/book/details", dependencies=[Depends(require_manager)])
async def get_book_details_endpoint(book_url: str):
    return await get_book_details(book_url)


@router.get("/category/full-books", dependencies=[Depends(require_manager)])
async def get_full_books_from_category_endpoint(
    category_url: str,
    limit: int | None = None,
    pagination: PaginationParams = Depends(),
):
    books = await get_full_books_from_category(
        category_url=category_url,
        limit=limit,
    )

    start = (pagination.page - 1) * pagination.page_size
    end = start + pagination.page_size

    return build_paginated_response(
        items=books[start:end],
        total=len(books),
        params=pagination,
    )


@router.post("/import/books", dependencies=[Depends(require_manager)])
async def import_category_endpoint(
    data: ImportCategoryRequest,
):
    task = celery_app.send_task(
        "import_books_from_category",
        kwargs={
            "category_name": data.category_name,
            "category_url": data.category_url,
            "limit": data.limit,
        },
    )

    return {
        "message": "Import started successfully.",
        "task_id": task.id,
    }


@router.post("/import/books/custom", dependencies=[Depends(require_manager)])
async def import_custom_books_endpoint(
    data: ImportCustomBooksRequest,
):
    task = celery_app.send_task(
        "import_custom_books",
        kwargs={
            "books": [book.model_dump() for book in data.books],
        },
    )

    return {
        "message": "Custom book import started successfully.",
        "task_id": task.id,
    }