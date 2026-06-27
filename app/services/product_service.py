import logging
from datetime import datetime, UTC

from bson import ObjectId
from bson.errors import InvalidId

from app.db.collections import get_product_collection, get_category_collection, get_author_collection
from app.exceptions.product import ProductNotFoundError, InvalidProductIdError, InvalidProductCategoryError, InvalidProductAuthorsError
from app.schemas.product import ProductCreate, ProductUpdate, ProductType
from app.services.discount_calculation_service import calculate_product_price


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


def parse_product_object_id(product_id: str):
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


async def create_product(product: ProductCreate):
    product_collection = get_product_collection()

    product_data = product.model_dump()
    product_data["price"] = float(product_data["price"])

    await validate_category_for_product(
        product_data["category_id"],
        product_data["product_type"],
    )

    if product.product_type == ProductType.BOOK:
        author_ids = product_data["book_details"]["author_ids"]
        await validate_authors_exist(author_ids)

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


async def get_active_products():
    product_collection = get_product_collection()

    products = await product_collection.find(
        {"is_active": True}
    ).to_list(length=100)

    return [await serialize_product(product) for product in products]


async def get_products():
    product_collection = get_product_collection()

    products = await product_collection.find().to_list(length=100)

    return [await serialize_product(product) for product in products]


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

    update_data = product.model_dump(exclude_unset=True)

    if "price" in update_data:
        update_data["price"] = float(update_data["price"])

    if not update_data:
        return await serialize_product(existing_product)

    if "category_id" in update_data:
        product_type = existing_product["product_type"]

        await validate_category_for_product(
            update_data["category_id"],
            product_type,
        )

    if "book_details" in update_data and update_data["book_details"] is not None:
        author_ids = update_data["book_details"]["author_ids"]
        await validate_authors_exist(author_ids)

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