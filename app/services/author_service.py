from app.db.collections import get_author_collection
from app.schemas.author import AuthorCreate, AuthorUpdate

from bson import ObjectId
from bson.errors import InvalidId

import logging
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


def serialize_author(author):
    return {
        "id": str(author["_id"]),
        "name": author["name"],
        "biography": author.get("biography"),
        "country": author.get("country"),
        "birth_date": author.get("birth_date"),
        "is_active": author["is_active"],
    }


async def create_author(author: AuthorCreate):
    author_data = author.model_dump()

    author_collection = get_author_collection()

    now = datetime.now(UTC)

    author_data["is_active"] = True
    author_data["created_at"] = now
    author_data["updated_at"] = now

    result = await author_collection.insert_one(author_data)

    created_author = await author_collection.find_one(
        {"_id": result.inserted_id}
    )

    logger.info("Author created: %s", author_data["name"])
    return serialize_author(created_author)


async def get_authors():
    author_collection = get_author_collection()

    authors = await author_collection.find().to_list(length=100)

    return [serialize_author(author) for author in authors]


async def get_author_by_id(author_id: str):
    author_collection = get_author_collection()

    try:
        object_id = ObjectId(author_id)
    except InvalidId:
        return None

    author = await author_collection.find_one(
        {"_id": object_id}
    )

    if not author:
        return None

    return serialize_author(author)


async def update_author(author_id: str, author: AuthorUpdate):
    author_collection = get_author_collection()

    try:
        object_id = ObjectId(author_id)
    except InvalidId:
        return None

    update_data = author.model_dump(exclude_unset=True)

    if not update_data:
        return await get_author_by_id(author_id)

    update_data["updated_at"] = datetime.now(UTC)

    result = await author_collection.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        return None

    updated_author = await author_collection.find_one(
        {"_id": object_id}
    )

    logger.info("Author updated: %s", author_id)
    return serialize_author(updated_author)


async def delete_author(author_id: str):
    author_collection = get_author_collection()

    try:
        object_id = ObjectId(author_id)
    except InvalidId:
        return None

    result = await author_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.now(UTC)
            }
        }
    )

    if result.matched_count == 0:
        return None

    deleted_author = await author_collection.find_one(
        {"_id": object_id}
    )

    logger.info("Author deactivated: %s", author_id)
    return serialize_author(deleted_author)