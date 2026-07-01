import logging
from datetime import datetime, UTC

from bson import ObjectId
from bson.errors import InvalidId

from app.db.collections import get_product_collection, get_category_collection, get_author_collection
from app.exceptions.product import ProductNotFoundError, InvalidProductIdError, InvalidProductCategoryError, InvalidProductAuthorsError, InvalidProductDetailsError, ProductIsbnAlreadyExistsError
from app.schemas.product import ProductCreate, ProductUpdate, ProductType
from app.services.discount_calculation_service import calculate_product_price

from app.utils.pagination import PaginationParams, build_paginated_response, get_skip

logger = logging.getLogger(__name__)


async def serialize_product(product: dict):
    price_data = await calculate_product_price(product)

    return {
        "id": str(product["_id"]),
        "name": product["name"],
        "description": product["description"],
        "price": product["price"],
        "original_price": price_data["original_price"],
        "final_price": price_data["final_price"],
        "active_discount": price_data["active_discount"],
        "stock_quantity": product["stock_quantity"],
        "category_id": product["category_id"],
        "product_type": product["product_type"],
        "book_details": product.get("book_details"),
        "is_active": product["is_active"],
        "created_at": product["created_at"],
        "updated_at": product["updated_at"],
    }


def parse_product_object_id(product_id: str) -> ObjectId:
    try:
        return ObjectId(product_id)
    except InvalidId as exc:
        raise InvalidProductIdError from exc


async def validate_category_for_product(category_id: str, product_type: str):
    category_collection = get_category_collection()

    try:
        object_id = ObjectId(category_id)
    except InvalidId as exc:
        raise InvalidProductCategoryError from exc

    category = await category_collection.find_one(
        {
            "_id": object_id,
            "is_active": True,
            "category_type": product_type,
        }
    )

    if not category:
        raise InvalidProductCategoryError


async def validate_authors_exist(author_ids: list[str]):
    if not author_ids:
        return

    if len(author_ids) != len(set(author_ids)):
        raise InvalidProductAuthorsError

    author_collection = get_author_collection()

    object_ids = []

    for author_id in author_ids:
        try:
            object_ids.append(ObjectId(author_id))
        except InvalidId as exc:
            raise InvalidProductAuthorsError from exc

    count = await author_collection.count_documents(
        {
            "_id": {"$in": object_ids},
            "is_active": True,
        }
    )

    if count != len(author_ids):
        raise InvalidProductAuthorsError


async def validate_unique_isbn(
    isbn: str | None,
    product_id: str | None = None,
):
    if not isbn:
        return

    product_collection = get_product_collection()

    query = {
        "book_details.isbn": isbn,
    }

    if product_id:
        query["_id"] = {"$ne": parse_product_object_id(product_id)}

    existing_product = await product_collection.find_one(query)

    if existing_product:
        raise ProductIsbnAlreadyExistsError


async def validate_book_details_for_create(product_data: dict):
    book_details = product_data.get("book_details") or {}

    author_ids = book_details.get("author_ids", [])
    await validate_authors_exist(author_ids)

    isbn = book_details.get("isbn")
    await validate_unique_isbn(isbn)


async def validate_book_details_for_update(existing_product: dict, update_data: dict, product_id: str):
    if "book_details" not in update_data:
        return

    if existing_product["product_type"] == ProductType.ACCESSORY:
        raise InvalidProductDetailsError

    existing_book_details = existing_product.get("book_details") or {}
    new_book_details = update_data.get("book_details") or {}

    merged_book_details = {
        **existing_book_details,
        **new_book_details,
    }

    author_ids = merged_book_details.get("author_ids", [])
    await validate_authors_exist(author_ids)

    isbn = merged_book_details.get("isbn")
    await validate_unique_isbn(isbn, product_id)

    update_data["book_details"] = merged_book_details


async def create_product(product: ProductCreate):
    product_collection = get_product_collection()

    product_data = product.model_dump()
    product_data["price"] = float(product_data["price"])

    await validate_category_for_product(
        product_data["category_id"],
        product_data["product_type"],
    )

    if product.product_type == ProductType.BOOK:
        await validate_book_details_for_create(product_data)

    now = datetime.now(UTC)

    product_data["is_active"] = True
    product_data["created_at"] = now
    product_data["updated_at"] = now

    result = await product_collection.insert_one(product_data)

    created_product = await product_collection.find_one(
        {"_id": result.inserted_id}
    )

    logger.info("Product created: %s", product_data["name"])

    return await serialize_product(created_product)


async def get_active_products(pagination: PaginationParams):
    product_collection = get_product_collection()

    query = {"is_active": True}

    total = await product_collection.count_documents(query)

    products = await product_collection.find(query).skip(
        get_skip(pagination)
    ).limit(
        pagination.page_size
    ).to_list(length=pagination.page_size)

    serialized_products = [
        await serialize_product(product)
        for product in products
    ]

    return build_paginated_response(
        items=serialized_products,
        total=total,
        params=pagination,
    )


async def get_products(pagination: PaginationParams):
    product_collection = get_product_collection()

    query = {}

    total = await product_collection.count_documents(query)

    products = await product_collection.find(query).skip(
        get_skip(pagination)
    ).limit(
        pagination.page_size
    ).to_list(length=pagination.page_size)

    serialized_products = [
        await serialize_product(product)
        for product in products
    ]

    return build_paginated_response(
        items=serialized_products,
        total=total,
        params=pagination,
    )


async def get_product_by_id(product_id: str):
    product_collection = get_product_collection()

    object_id = parse_product_object_id(product_id)

    product = await product_collection.find_one({"_id": object_id})

    if not product:
        raise ProductNotFoundError

    return await serialize_product(product)


async def update_product(product_id: str, product: ProductUpdate):
    product_collection = get_product_collection()

    object_id = parse_product_object_id(product_id)

    existing_product = await product_collection.find_one({"_id": object_id})

    if not existing_product:
        raise ProductNotFoundError

    update_data = product.model_dump(exclude_unset=True, exclude_none=True)

    if not update_data:
        return await serialize_product(existing_product)

    if "price" in update_data:
        update_data["price"] = float(update_data["price"])

    if "category_id" in update_data:
        await validate_category_for_product(
            update_data["category_id"],
            existing_product["product_type"],
        )

    await validate_book_details_for_update(
        existing_product=existing_product,
        update_data=update_data,
        product_id=product_id,
    )

    update_data["updated_at"] = datetime.now(UTC)

    await product_collection.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    updated_product = await product_collection.find_one({"_id": object_id})

    logger.info("Product updated: %s", product_id)

    return await serialize_product(updated_product)


async def delete_product(product_id: str):
    product_collection = get_product_collection()

    object_id = parse_product_object_id(product_id)

    result = await product_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.now(UTC),
            }
        },
    )

    if result.matched_count == 0:
        raise ProductNotFoundError

    deleted_product = await product_collection.find_one({"_id": object_id})

    logger.info("Product deactivated: %s", product_id)

    return await serialize_product(deleted_product)