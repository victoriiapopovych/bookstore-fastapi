from app.db.collections import get_category_collection
from app.schemas.category import CategoryCreate, CategoryUpdate

from bson import ObjectId
from bson.errors import InvalidId

import logging
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


def serialize_category(category):
    return {
        "id": str(category["_id"]),
        "name": category["name"],
        "slug": category["slug"],
        "category_type": category["category_type"],
        "description": category.get("description"),
        "parent_id": category.get("parent_id"),
        "is_active": category["is_active"],
        "created_at": category["created_at"],
        "updated_at": category["updated_at"]
    }


async def validate_parent_category(parent_id: str | None):
    if parent_id is None:
        return True

    category_collection = get_category_collection()

    try:
        object_id = ObjectId(parent_id)
    except InvalidId:
        return False

    parent_category = await category_collection.find_one(
        {"_id": object_id, "is_active": True}
    )

    return parent_category is not None


async def validate_unique_slug(slug: str, category_id: str | None = None):
    category_collection = get_category_collection()

    query = {"slug": slug}

    if category_id:
        try:
            object_id = ObjectId(category_id)
        except InvalidId:
            return False

        query["_id"] = {"$ne": object_id}

    existing_category = await category_collection.find_one(query)

    return existing_category is None


async def create_category(category: CategoryCreate):
    category_data = category.model_dump()

    category_collection = get_category_collection()

    is_parent_valid = await validate_parent_category(category_data.get("parent_id"))

    if not is_parent_valid:
        return None
    
    is_slug_unique = await validate_unique_slug(category_data["slug"])

    if not is_slug_unique:
        return None

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



async def get_categories():
    category_collection = get_category_collection()

    categories = await category_collection.find().to_list(length=100)

    return [serialize_category(category) for category in categories]


async def get_category_by_id(category_id: str):
    category_collection = get_category_collection()

    try:
        object_id = ObjectId(category_id)
    except InvalidId:
        return None

    category = await category_collection.find_one(
        {"_id": object_id}
    )

    if not category:
        return None

    return serialize_category(category)


async def update_category(category_id: str, category: CategoryUpdate):
    category_collection = get_category_collection()

    try:
        object_id = ObjectId(category_id)
    except InvalidId:
        return None

    update_data = category.model_dump(exclude_unset=True)

    if "slug" in update_data:
        is_slug_unique = await validate_unique_slug(update_data["slug"], category_id)

        if not is_slug_unique:
            return None

    if "parent_id" in update_data:
        is_parent_valid = await validate_parent_category(update_data["parent_id"])

        if not is_parent_valid:
            return None

    if not update_data:
        return await get_category_by_id(category_id)

    update_data["updated_at"] = datetime.now(UTC)

    result = await category_collection.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        return None

    updated_category = await category_collection.find_one(
        {"_id": object_id}
    )

    logger.info("Category updated: %s", category_id)
    return serialize_category(updated_category)


async def delete_category(category_id: str):
    category_collection = get_category_collection()

    try:
        object_id = ObjectId(category_id)
    except InvalidId:
        return None

    result = await category_collection.update_one(
        {"_id": object_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(UTC)}}
    )

    if result.matched_count == 0:
        return None

    deleted_category = await category_collection.find_one(
        {"_id": object_id}
    )

    logger.info("Category deactivated: %s", category_id)
    return serialize_category(deleted_category)