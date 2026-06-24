from app.db.collections import get_product_collection, get_category_collection, get_author_collection
from app.schemas.product import ProductCreate, ProductUpdate, ProductType

from app.services.discount_calculation_service import calculate_product_price

from bson import ObjectId
from bson.errors import InvalidId

import logging
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


async def serialize_product(product):
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


async def validate_category_for_product(category_id: str, product_type: str):
    category_collection = get_category_collection()

    try:
        object_id = ObjectId(category_id)
    except InvalidId:
        return False

    category = await category_collection.find_one({
        "_id": object_id,
        "is_active": True,
        "category_type": product_type,
    })

    return category is not None


async def validate_authors_exist(author_ids: list[str]):
    if len(author_ids) != len(set(author_ids)):
        return False

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
    product_data["price"] = float(product_data["price"])

    category_exists = await validate_category_for_product(
        product_data["category_id"],
        product_data["product_type"],
    )

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
    return await serialize_product(created_product)


async def get_products():
    product_collection = get_product_collection()

    products = await product_collection.find().to_list(length=100)

    return [await serialize_product(product) for product in products]


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

    return await serialize_product(product)


async def update_product(product_id: str, product: ProductUpdate):
    product_collection = get_product_collection()

    try:
        object_id = ObjectId(product_id)
    except InvalidId:
        return None

    update_data = product.model_dump(exclude_unset=True)

    if "price" in update_data:
        update_data["price"] = float(update_data["price"])

    if not update_data:
        return await get_product_by_id(product_id)

    if "category_id" in update_data:
        existing_product = await product_collection.find_one({"_id": object_id})

        if not existing_product:
            return None

        product_type = existing_product["product_type"]

        category_exists = await validate_category_for_product(
            update_data["category_id"],
            product_type,
        )

        if not category_exists:
            return None
        
    if "book_details" in update_data and update_data["book_details"] is not None:
        author_ids = update_data["book_details"]["author_ids"]

        authors_exist = await validate_authors_exist(author_ids)

        if not authors_exist:
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
    return await serialize_product(updated_product)


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
    return await serialize_product(deleted_product)