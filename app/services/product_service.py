from app.db.collections import get_product_collection, get_category_collection, get_author_collection
from app.schemas.product import ProductCreate, ProductUpdate, ProductType

from bson import ObjectId
from bson.errors import InvalidId

import logging
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


def serialize_product(product):
    return {
        "id": str(product["_id"]),
        "name": product["name"],
        "description": product["description"],
        "price": product["price"],
        "stock_quantity": product["stock_quantity"],
        "category_id": product["category_id"],
        "product_type": product["product_type"],
        "book_details": product.get("book_details"),
        "is_active": product["is_active"],
    }


async def validate_category_exists(category_id: str):
    category_collection = get_category_collection()

    try:
        object_id = ObjectId(category_id)
    except InvalidId:
        return False

    category = await category_collection.find_one({
        "_id": object_id,
        "is_active": True,
    })

    return category is not None


async def validate_authors_exist(author_ids: list[str]):
    author_collection = get_author_collection()

    object_ids = []

    for author_id in author_ids:
        try:
            object_ids.append(ObjectId(author_id))
        except InvalidId:
            return False

    count = await author_collection.count_documents({
        "_id": {"$in": object_ids},
        "is_active": True,
    })

    return count == len(author_ids)


async def create_product(product: ProductCreate):
    product_collection = get_product_collection()

    product_data = product.model_dump()

    category_exists = await validate_category_exists(product_data["category_id"])

    if not category_exists:
        return None

    if product.product_type == ProductType.BOOK:
        author_ids = product_data["book_details"]["author_ids"]

        authors_exist = await validate_authors_exist(author_ids)

        if not authors_exist:
            return None

    now = datetime.now(UTC)

    product_data["is_active"] = True
    product_data["created_at"] = now
    product_data["updated_at"] = now

    result = await product_collection.insert_one(product_data)

    created_product = await product_collection.find_one(
        {"_id": result.inserted_id}
    )

    logger.info("Product created: %s", product_data["name"])
    return serialize_product(created_product)


async def get_products():
    product_collection = get_product_collection()

    products = await product_collection.find().to_list(length=100)

    return [serialize_product(product) for product in products]


async def get_product_by_id(product_id: str):
    product_collection = get_product_collection()

    try:
        object_id = ObjectId(product_id)
    except InvalidId:
        return None

    product = await product_collection.find_one(
        {"_id": object_id}
    )

    if not product:
        return None

    return serialize_product(product)


async def update_product(product_id: str, product: ProductUpdate):
    product_collection = get_product_collection()

    try:
        object_id = ObjectId(product_id)
    except InvalidId:
        return None

    update_data = product.model_dump(exclude_unset=True)

    if not update_data:
        return await get_product_by_id(product_id)

    if "category_id" in update_data:
        category_exists = await validate_category_exists(update_data["category_id"])

        if not category_exists:
            return None

    update_data["updated_at"] = datetime.now(UTC)

    result = await product_collection.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        return None

    updated_product = await product_collection.find_one(
        {"_id": object_id}
    )

    logger.info("Product updated: %s", product_id)
    return serialize_product(updated_product)


async def delete_product(product_id: str):
    product_collection = get_product_collection()

    try:
        object_id = ObjectId(product_id)
    except InvalidId:
        return None

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
        return None

    deleted_product = await product_collection.find_one(
        {"_id": object_id}
    )

    logger.info("Product deactivated: %s", product_id)
    return serialize_product(deleted_product)