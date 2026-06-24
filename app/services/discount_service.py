from datetime import datetime, UTC
import logging

from bson import ObjectId
from bson.errors import InvalidId

from app.db.collections import get_discount_collection, get_product_collection, get_category_collection, get_bundle_collection
from app.schemas.discount import DiscountCreate, DiscountUpdate, DiscountTargetType


logger = logging.getLogger(__name__)


def serialize_discount(discount):
    return {
        "id": str(discount["_id"]),
        "name": discount["name"],
        "discount_type": discount["discount_type"],
        "value": discount["value"],
        "target_type": discount["target_type"],
        "target_id": discount["target_id"],
        "start_date": discount["start_date"],
        "end_date": discount["end_date"],
        "is_active": discount["is_active"],
        "created_at": discount["created_at"],
        "updated_at": discount["updated_at"],
    }


async def validate_discount_target(target_type: DiscountTargetType, target_id: str):
    try:
        object_id = ObjectId(target_id)
    except InvalidId:
        return False

    if target_type == DiscountTargetType.PRODUCT:
        collection = get_product_collection()
    elif target_type == DiscountTargetType.CATEGORY:
        collection = get_category_collection()
    elif target_type == DiscountTargetType.BUNDLE:
        collection = get_bundle_collection()
    else:
        return False

    target = await collection.find_one(
        {
            "_id": object_id,
            "is_active": True,
        }
    )

    return target is not None


async def create_discount(discount: DiscountCreate):
    discount_collection = get_discount_collection()

    discount_data = discount.model_dump()
    discount_data["value"] = float(discount_data["value"])

    is_target_valid = await validate_discount_target(
        discount_data["target_type"],
        discount_data["target_id"],
    )

    if not is_target_valid:
        return None

    now = datetime.now(UTC)

    discount_data["is_active"] = True
    discount_data["created_at"] = now
    discount_data["updated_at"] = now

    result = await discount_collection.insert_one(discount_data)

    created_discount = await discount_collection.find_one(
        {"_id": result.inserted_id}
    )

    logger.info("Discount created: %s", discount_data["name"])

    return serialize_discount(created_discount)


async def get_discounts():
    discount_collection = get_discount_collection()

    discounts = await discount_collection.find().to_list(length=100)

    return [serialize_discount(discount) for discount in discounts]


async def get_discount_by_id(discount_id: str):
    discount_collection = get_discount_collection()

    try:
        object_id = ObjectId(discount_id)
    except InvalidId:
        return None

    discount = await discount_collection.find_one({"_id": object_id})

    if not discount:
        return None

    return serialize_discount(discount)


async def update_discount(discount_id: str, discount: DiscountUpdate):
    discount_collection = get_discount_collection()

    try:
        object_id = ObjectId(discount_id)
    except InvalidId:
        return None

    existing_discount = await discount_collection.find_one({"_id": object_id})

    if not existing_discount:
        return None

    update_data = discount.model_dump(exclude_unset=True)

    if not update_data:
        return serialize_discount(existing_discount)

    target_type = update_data.get("target_type", existing_discount["target_type"])
    target_id = update_data.get("target_id", existing_discount["target_id"])

    if "target_type" in update_data or "target_id" in update_data:
        is_target_valid = await validate_discount_target(target_type, target_id)

        if not is_target_valid:
            return None

    if "value" in update_data:
        update_data["value"] = float(update_data["value"])

    update_data["updated_at"] = datetime.now(UTC)

    result = await discount_collection.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        return None

    updated_discount = await discount_collection.find_one({"_id": object_id})

    logger.info("Discount updated: %s", discount_id)

    return serialize_discount(updated_discount)


async def delete_discount(discount_id: str):
    discount_collection = get_discount_collection()

    try:
        object_id = ObjectId(discount_id)
    except InvalidId:
        return None

    result = await discount_collection.update_one(
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

    deleted_discount = await discount_collection.find_one({"_id": object_id})

    logger.info("Discount deactivated: %s", discount_id)

    return serialize_discount(deleted_discount)