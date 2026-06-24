from datetime import datetime, UTC

from bson import ObjectId
from bson.errors import InvalidId

from app.core.security import hash_password, verify_password
from app.db.collections import get_user_collection
from app.schemas.user import UserRegister, UserUpdate, UserRole

import logging

logger = logging.getLogger(__name__)


def serialize_user(user):
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "is_active": user["is_active"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }


async def get_user_by_email(email: str):
    user_collection = get_user_collection()
    return await user_collection.find_one({"email": email.lower()})


async def get_user_by_id(user_id: str):
    user_collection = get_user_collection()

    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        return None

    return await user_collection.find_one(
        {"_id": object_id, "is_active": True}
    )


async def register_user(user: UserRegister):
    user_collection = get_user_collection()

    existing_user = await get_user_by_email(user.email)
    if existing_user:
        return None

    user_data = user.model_dump()
    password = user_data.pop("password")

    now = datetime.now(UTC)

    user_data["email"] = user_data["email"].lower()
    user_data["hashed_password"] = hash_password(password)
    user_data["role"] = UserRole.CUSTOMER.value
    user_data["is_active"] = True
    user_data["created_at"] = now
    user_data["updated_at"] = now

    result = await user_collection.insert_one(user_data)

    created_user = await user_collection.find_one(
        {"_id": result.inserted_id}
    )

    logger.info("User registered: %s", user_data["email"])
    return serialize_user(created_user)


async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)

    if not user:
        return None

    if not user["is_active"]:
        return None

    if not verify_password(password, user["hashed_password"]):
        return None

    return user


async def get_users():
    user_collection = get_user_collection()

    users = await user_collection.find().to_list(length=100)

    return [serialize_user(user) for user in users]


async def update_user(user_id: str, user: UserUpdate):
    user_collection = get_user_collection()

    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        return None

    update_data = user.model_dump(exclude_unset=True)

    if not update_data:
        existing_user = await get_user_by_id(user_id)
        return serialize_user(existing_user) if existing_user else None

    if "password" in update_data:
        password = update_data.pop("password")
        update_data["hashed_password"] = hash_password(password)

    update_data["updated_at"] = datetime.now(UTC)

    result = await user_collection.update_one(
        {"_id": object_id, "is_active": True},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        return None

    updated_user = await user_collection.find_one({"_id": object_id})

    return serialize_user(updated_user)


async def delete_user(user_id: str):
    user_collection = get_user_collection()

    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        return None

    result = await user_collection.update_one(
        {"_id": object_id, "is_active": True},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.now(UTC),
            }
        },
    )

    if result.matched_count == 0:
        return None

    deleted_user = await user_collection.find_one({"_id": object_id})

    logger.info("User deactivated: %s", user_id)
    return serialize_user(deleted_user)