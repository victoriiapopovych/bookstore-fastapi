from decimal import Decimal
from datetime import datetime, UTC
import logging

from bson import ObjectId
from bson.errors import InvalidId

from app.db.collections import get_bundle_collection, get_product_collection
from app.schemas.bundle import BundleCreate, BundleUpdate

from app.services.discount_calculation_service import calculate_bundle_price


logger = logging.getLogger(__name__)


async def serialize_bundle(bundle):
    price_data = await calculate_bundle_price(bundle)

    return {
        "id": str(bundle["_id"]),
        "name": bundle["name"],
        "description": bundle["description"],
        "items": bundle["items"],
        "discount_percent": bundle["discount_percent"],
        "original_price": bundle["original_price"],
        "final_price": bundle["final_price"],
        "discounted_price": price_data["final_price"],
        "active_discount": price_data["active_discount"],
        "is_active": bundle["is_active"],
        "created_at": bundle["created_at"],
        "updated_at": bundle["updated_at"],
    }


async def calculate_bundle_prices(items: list[dict], discount_percent: int):
    product_collection = get_product_collection()

    product_ids = []

    for item in items:
        try:
            product_ids.append(ObjectId(item["product_id"]))
        except InvalidId:
            return None

    products = await product_collection.find(
        {
            "_id": {"$in": product_ids},
            "is_active": True,
        }
    ).to_list(length=100)

    products_by_id = {str(product["_id"]): product for product in products}

    if len(products_by_id) != len(set(item["product_id"] for item in items)):
        return None

    original_price = Decimal("0")

    for item in items:
        product = products_by_id.get(item["product_id"])

        if not product:
            return None

        original_price += Decimal(str(product["price"])) * item["quantity"]

    discount_amount = original_price * Decimal(discount_percent) / Decimal(100)
    final_price = original_price - discount_amount

    return original_price, final_price


async def create_bundle(bundle: BundleCreate):
    bundle_collection = get_bundle_collection()

    bundle_data = bundle.model_dump()

    prices = await calculate_bundle_prices(
        bundle_data["items"],
        bundle_data["discount_percent"],
    )

    if not prices:
        return None

    original_price, final_price = prices

    now = datetime.now(UTC)

    bundle_data["original_price"] = float(original_price)
    bundle_data["final_price"] = float(final_price)
    bundle_data["is_active"] = True
    bundle_data["created_at"] = now
    bundle_data["updated_at"] = now

    result = await bundle_collection.insert_one(bundle_data)

    created_bundle = await bundle_collection.find_one(
        {"_id": result.inserted_id}
    )

    logger.info("Bundle created: %s", bundle_data["name"])
    return await serialize_bundle(created_bundle)


async def get_bundles():
    bundle_collection = get_bundle_collection()

    bundles = await bundle_collection.find().to_list(length=100)

    return [await serialize_bundle(bundle) for bundle in bundles]


async def get_bundle_by_id(bundle_id: str):
    bundle_collection = get_bundle_collection()

    try:
        object_id = ObjectId(bundle_id)
    except InvalidId:
        return None

    bundle = await bundle_collection.find_one({"_id": object_id})

    if not bundle:
        return None

    return await serialize_bundle(bundle)


async def update_bundle(bundle_id: str, bundle: BundleUpdate):
    bundle_collection = get_bundle_collection()

    try:
        object_id = ObjectId(bundle_id)
    except InvalidId:
        return None

    existing_bundle = await bundle_collection.find_one({"_id": object_id})

    if not existing_bundle:
        return None

    update_data = bundle.model_dump(exclude_unset=True)

    if not update_data:
        return await serialize_bundle(existing_bundle)

    items = update_data.get("items", existing_bundle["items"])
    discount_percent = update_data.get(
        "discount_percent",
        existing_bundle["discount_percent"],
    )

    if "items" in update_data or "discount_percent" in update_data:
        prices = await calculate_bundle_prices(items, discount_percent)

        if not prices:
            return None

        original_price, final_price = prices

        update_data["original_price"] = float(original_price)
        update_data["final_price"] = float(final_price)

    update_data["updated_at"] = datetime.now(UTC)

    result = await bundle_collection.update_one(
        {"_id": object_id},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        return None

    updated_bundle = await bundle_collection.find_one({"_id": object_id})

    logger.info("Bundle updated: %s", bundle_id)
    return await serialize_bundle(updated_bundle)


async def delete_bundle(bundle_id: str):
    bundle_collection = get_bundle_collection()

    try:
        object_id = ObjectId(bundle_id)
    except InvalidId:
        return None

    result = await bundle_collection.update_one(
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

    deleted_bundle = await bundle_collection.find_one({"_id": object_id})

    logger.info("Bundle deactivated: %s", bundle_id)
    return await serialize_bundle(deleted_bundle)