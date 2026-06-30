import logging
from datetime import datetime, UTC

from bson import ObjectId
from bson.errors import InvalidId

from app.db.collections import get_author_collection
from app.exceptions.author import AuthorNotFoundError, InvalidAuthorIdError
from app.schemas.author import AuthorCreate, AuthorUpdate


logger = logging.getLogger(__name__)


def serialize_author(author):
    return {
        "id": str(author["_id"]),
        "name": author["name"],
        "biography": author.get("biography"),
        "country": author.get("country"),
        "birth_date": author.get("birth_date"),
        "is_active": author["is_active"],
        "created_at": author["created_at"],
        "updated_at": author["updated_at"],
    }


def parse_author_object_id(author_id: str):
    try:
        return ObjectId(author_id)
    except InvalidId as exc:
        raise InvalidAuthorIdError from exc


def convert_birth_date_to_datetime(data: dict):
    if data.get("birth_date"):
        data["birth_date"] = datetime.combine(
            data["birth_date"],
            datetime.min.time(),
        )


async def create_author(author: AuthorCreate):
    author_collection = get_author_collection()

    author_data = author.model_dump()
    convert_birth_date_to_datetime(author_data)

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


async def get_active_authors():
    author_collection = get_author_collection()

    authors = await author_collection.find(
        {"is_active": True}
    ).to_list(length=100)

    return [serialize_author(author) for author in authors]


async def get_authors():
    author_collection = get_author_collection()

    authors = await author_collection.find().to_list(length=100)

    return [serialize_author(author) for author in authors]


async def get_author_by_id(author_id: str):
    author_collection = get_author_collection()

    object_id = parse_author_object_id(author_id)

    author = await author_collection.find_one({"_id": object_id})

    if not author:
        raise AuthorNotFoundError

    return serialize_author(author)


async def update_author(author_id: str, author: AuthorUpdate):
    author_collection = get_author_collection()

    object_id = parse_author_object_id(author_id)

    update_data = author.model_dump(exclude_unset=True)
    convert_birth_date_to_datetime(update_data)

    if not update_data:
        return await get_author_by_id(author_id)

    update_data["updated_at"] = datetime.now(UTC)

    result = await author_collection.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        raise AuthorNotFoundError

    updated_author = await author_collection.find_one({"_id": object_id})

    logger.info("Author updated: %s", author_id)
    return serialize_author(updated_author)


async def delete_author(author_id: str):
    author_collection = get_author_collection()

    object_id = parse_author_object_id(author_id)

    result = await author_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.now(UTC),
            }
        },
    )

    if result.matched_count == 0:
        raise AuthorNotFoundError

    deleted_author = await author_collection.find_one({"_id": object_id})

    logger.info("Author deactivated: %s", author_id)
    return serialize_author(deleted_author)