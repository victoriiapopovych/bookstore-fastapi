from datetime import datetime, UTC
import logging

from bson import ObjectId
from bson.errors import InvalidId

from app.db.collections import get_discount_collection, get_product_collection, get_category_collection, get_bundle_collection
from app.exceptions.discount import DiscountNotFoundError, InvalidDiscountIdError, InvalidDiscountTargetError, DiscountOverlapError
from app.schemas.discount import DiscountCreate, DiscountUpdate, DiscountTargetType

from app.utils.pagination import PaginationParams, build_paginated_response, get_skip


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


def parse_discount_object_id(discount_id: str):
    try:
        return ObjectId(discount_id)
    except InvalidId as exc:
        raise InvalidDiscountIdError from exc


async def validate_discount_target(target_type: DiscountTargetType, target_id: str):
    try:
        object_id = ObjectId(target_id)
    except InvalidId as exc:
        raise InvalidDiscountTargetError from exc

    if target_type == DiscountTargetType.PRODUCT:
        collection = get_product_collection()
    elif target_type == DiscountTargetType.CATEGORY:
        collection = get_category_collection()
    elif target_type == DiscountTargetType.BUNDLE:
        collection = get_bundle_collection()
    else:
        raise InvalidDiscountTargetError

    target = await collection.find_one(
        {"_id": object_id, "is_active": True}
    )

    if not target:
        raise InvalidDiscountTargetError
    

async def validate_discount_period_overlap(
    target_type: DiscountTargetType,
    target_id: str,
    start_date: datetime,
    end_date: datetime,
    discount_id: str | None = None,
):
    discount_collection = get_discount_collection()

    query = {
        "target_type": target_type,
        "target_id": target_id,
        "is_active": True,
        "start_date": {"$lt": end_date},
        "end_date": {"$gt": start_date},
    }

    if discount_id:
        query["_id"] = {"$ne": parse_discount_object_id(discount_id)}

    existing_discount = await discount_collection.find_one(query)

    if existing_discount:
        raise DiscountOverlapError


async def create_discount(discount: DiscountCreate):
    discount_collection = get_discount_collection()

    discount_data = discount.model_dump()
    discount_data["value"] = float(discount_data["value"])

    await validate_discount_target(
        discount_data["target_type"],
        discount_data["target_id"],
    )

    await validate_discount_period_overlap(
        discount_data["target_type"],
        discount_data["target_id"],
        discount_data["start_date"],
        discount_data["end_date"],
    )

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


async def get_active_discounts(pagination: PaginationParams):
    discount_collection = get_discount_collection()
    now = datetime.now(UTC)

    query = {
        "is_active": True,
        "start_date": {"$lte": now},
        "end_date": {"$gte": now},
    }

    total = await discount_collection.count_documents(query)

    discounts = await discount_collection.find(query).skip(
        get_skip(pagination)
    ).limit(
        pagination.page_size
    ).to_list(length=pagination.page_size)

    serialized_discounts = [
        serialize_discount(discount)
        for discount in discounts
    ]

    return build_paginated_response(
        items=serialized_discounts,
        total=total,
        params=pagination,
    )


async def get_discounts(pagination: PaginationParams):
    discount_collection = get_discount_collection()

    query = {}

    total = await discount_collection.count_documents(query)

    discounts = await discount_collection.find(query).skip(
        get_skip(pagination)
    ).limit(
        pagination.page_size
    ).to_list(length=pagination.page_size)

    serialized_discounts = [
        serialize_discount(discount)
        for discount in discounts
    ]

    return build_paginated_response(
        items=serialized_discounts,
        total=total,
        params=pagination,
    )


async def get_discount_by_id(discount_id: str):
    discount_collection = get_discount_collection()

    object_id = parse_discount_object_id(discount_id)

    discount = await discount_collection.find_one({"_id": object_id})

    if not discount:
        raise DiscountNotFoundError

    return serialize_discount(discount)


async def update_discount(discount_id: str, discount: DiscountUpdate):
    discount_collection = get_discount_collection()

    object_id = parse_discount_object_id(discount_id)

    existing_discount = await discount_collection.find_one({"_id": object_id})

    if not existing_discount:
        raise DiscountNotFoundError

    update_data = discount.model_dump(exclude_unset=True)

    if not update_data:
        return serialize_discount(existing_discount)

    target_type = update_data.get("target_type", existing_discount["target_type"])
    target_id = update_data.get("target_id", existing_discount["target_id"])

    if "target_type" in update_data or "target_id" in update_data:
        await validate_discount_target(target_type, target_id)

    start_date = update_data.get("start_date", existing_discount["start_date"])
    end_date = update_data.get("end_date", existing_discount["end_date"])

    await validate_discount_period_overlap(
        target_type,
        target_id,
        start_date,
        end_date,
        discount_id,
    )

    if "value" in update_data:
        update_data["value"] = float(update_data["value"])

    update_data["updated_at"] = datetime.now(UTC)

    await discount_collection.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    updated_discount = await discount_collection.find_one({"_id": object_id})

    logger.info("Discount updated: %s", discount_id)
    return serialize_discount(updated_discount)


async def delete_discount(discount_id: str):
    discount_collection = get_discount_collection()

    object_id = parse_discount_object_id(discount_id)

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
        raise DiscountNotFoundError

    deleted_discount = await discount_collection.find_one({"_id": object_id})

    logger.info("Discount deactivated: %s", discount_id)
    return serialize_discount(deleted_discount)


async def deactivate_expired_discounts():
    discount_collection = get_discount_collection()
    now = datetime.now(UTC)

    result = await discount_collection.update_many(
        {
            "is_active": True,
            "end_date": {"$lt": now},
        },
        {
            "$set": {
                "is_active": False,
                "updated_at": now,
            }
        },
    )

    logger.info("Expired discounts deactivated: %s", result.modified_count)

    return result.modified_count