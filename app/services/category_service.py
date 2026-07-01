import logging
from datetime import datetime, UTC

from bson import ObjectId
from bson.errors import InvalidId

from app.db.collections import get_category_collection
from app.exceptions.category import CategoryNotFoundError, InvalidCategoryIdError, InvalidParentCategoryError, CategorySlugAlreadyExistsError
from app.schemas.category import CategoryCreate, CategoryUpdate

from app.utils.pagination import PaginationParams, build_paginated_response, get_skip


logger = logging.getLogger(__name__)


def serialize_category(category):
    return {
        "id": str(category["_id"]),
        "name": category["name"],
        "slug": category["slug"],
        "category_type": category["category_type"],
        "description": category.get("description"),
        "is_active": category["is_active"],
        "created_at": category.get("created_at"),
        "updated_at": category.get("updated_at"),
        "parent_id": category.get("parent_id"),
    }


def parse_object_id(object_id: str):
    try:
        return ObjectId(object_id)
    except InvalidId as exc:
        raise InvalidCategoryIdError from exc


async def validate_parent_category(parent_id: str | None):
    if parent_id is None:
        return

    category_collection = get_category_collection()

    try:
        object_id = ObjectId(parent_id)
    except InvalidId as exc:
        raise InvalidParentCategoryError from exc

    parent_category = await category_collection.find_one(
        {"_id": object_id, "is_active": True}
    )

    if not parent_category:
        raise InvalidParentCategoryError


async def validate_unique_slug(slug: str, category_id: str | None = None):
    category_collection = get_category_collection()

    query = {"slug": slug}

    if category_id:
        object_id = parse_object_id(category_id)
        query["_id"] = {"$ne": object_id}

    existing_category = await category_collection.find_one(query)

    if existing_category:
        raise CategorySlugAlreadyExistsError


async def create_category(category: CategoryCreate):
    category_collection = get_category_collection()
    category_data = category.model_dump()

    await validate_parent_category(category_data.get("parent_id"))
    await validate_unique_slug(category_data["slug"])

    now = datetime.now(UTC)

    category_data["is_active"] = True
    category_data["created_at"] = now
    category_data["updated_at"] = now

    result = await category_collection.insert_one(category_data)

    created_category = await category_collection.find_one(
        {"_id": result.inserted_id}
    )

    logger.info("Category created: %s", category_data["slug"])
    return serialize_category(created_category)


async def get_active_categories(pagination: PaginationParams):
    category_collection = get_category_collection()

    query = {"is_active": True}

    total = await category_collection.count_documents(query)

    categories = await category_collection.find(query).skip(
        get_skip(pagination)
    ).limit(
        pagination.page_size
    ).to_list(length=pagination.page_size)

    serialized_categories = [
        serialize_category(category)
        for category in categories
    ]

    return build_paginated_response(
        items=serialized_categories,
        total=total,
        params=pagination,
    )


async def get_categories(pagination: PaginationParams):
    category_collection = get_category_collection()

    query = {}

    total = await category_collection.count_documents(query)

    categories = await category_collection.find(query).skip(
        get_skip(pagination)
    ).limit(
        pagination.page_size
    ).to_list(length=pagination.page_size)

    serialized_categories = [
        serialize_category(category)
        for category in categories
    ]

    return build_paginated_response(
        items=serialized_categories,
        total=total,
        params=pagination,
    )


async def get_category_by_id(category_id: str):
    category_collection = get_category_collection()

    object_id = parse_object_id(category_id)

    category = await category_collection.find_one({"_id": object_id})

    if not category:
        raise CategoryNotFoundError

    return serialize_category(category)


async def update_category(category_id: str, category: CategoryUpdate):
    category_collection = get_category_collection()

    object_id = parse_object_id(category_id)
    update_data = category.model_dump(exclude_unset=True)

    if "slug" in update_data:
        await validate_unique_slug(update_data["slug"], category_id)

    if "parent_id" in update_data:
        await validate_parent_category(update_data["parent_id"])

    if not update_data:
        return await get_category_by_id(category_id)

    update_data["updated_at"] = datetime.now(UTC)

    result = await category_collection.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        raise CategoryNotFoundError

    updated_category = await category_collection.find_one({"_id": object_id})

    logger.info("Category updated: %s", category_id)
    return serialize_category(updated_category)


async def delete_category(category_id: str):
    category_collection = get_category_collection()

    object_id = parse_object_id(category_id)

    result = await category_collection.update_one(
        {"_id": object_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(UTC)}},
    )

    if result.matched_count == 0:
        raise CategoryNotFoundError

    deleted_category = await category_collection.find_one({"_id": object_id})

    logger.info("Category deactivated: %s", category_id)
    return serialize_category(deleted_category)