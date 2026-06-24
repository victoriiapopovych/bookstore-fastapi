from datetime import datetime, UTC
from decimal import Decimal

from app.db.collections import get_discount_collection
from app.schemas.discount import DiscountType, DiscountTargetType


def serialize_active_discount(discount):
    return {
        "id": str(discount["_id"]),
        "name": discount["name"],
        "discount_type": discount["discount_type"],
        "value": discount["value"],
    }


def calculate_discounted_price(price: float | Decimal, discount: dict | None):
    original_price = Decimal(str(price))

    if not discount:
        return {
            "original_price": float(original_price),
            "final_price": float(original_price),
            "active_discount": None,
        }

    discount_value = Decimal(str(discount["value"]))

    if discount["discount_type"] == DiscountType.PERCENTAGE:
        discount_amount = original_price * discount_value / Decimal(100)

    elif discount["discount_type"] == DiscountType.FIXED:
        discount_amount = discount_value

    else:
        discount_amount = Decimal(0)

    final_price = original_price - discount_amount

    if final_price < 0:
        final_price = Decimal(0)

    return {
        "original_price": float(original_price),
        "final_price": float(final_price),
        "active_discount": serialize_active_discount(discount),
    }


async def get_active_discount_for_product(product: dict):
    discount_collection = get_discount_collection()
    now = datetime.now(UTC)

    discounts = await discount_collection.find(
        {
            "is_active": True,
            "start_date": {"$lte": now},
            "end_date": {"$gte": now},
            "$or": [
                {
                    "target_type": DiscountTargetType.PRODUCT,
                    "target_id": str(product["_id"]),
                },
                {
                    "target_type": DiscountTargetType.CATEGORY,
                    "target_id": product["category_id"],
                },
            ],
        }
    ).to_list(length=100)

    if not discounts:
        return None

    best_discount = None
    best_price = Decimal(str(product["price"]))

    for discount in discounts:
        calculated = calculate_discounted_price(product["price"], discount)
        final_price = Decimal(str(calculated["final_price"]))

        if final_price < best_price:
            best_price = final_price
            best_discount = discount

    return best_discount


async def calculate_product_price(product: dict):
    discount = await get_active_discount_for_product(product)

    return calculate_discounted_price(
        product["price"],
        discount,
    )


async def get_active_discount_for_bundle(bundle: dict):
    discount_collection = get_discount_collection()
    now = datetime.now(UTC)

    discounts = await discount_collection.find(
        {
            "is_active": True,
            "target_type": DiscountTargetType.BUNDLE,
            "target_id": str(bundle["_id"]),
            "start_date": {"$lte": now},
            "end_date": {"$gte": now},
        }
    ).to_list(length=100)

    if not discounts:
        return None

    best_discount = None
    best_price = Decimal(str(bundle["final_price"]))

    for discount in discounts:
        calculated = calculate_discounted_price(bundle["final_price"], discount)
        final_price = Decimal(str(calculated["final_price"]))

        if final_price < best_price:
            best_price = final_price
            best_discount = discount

    return best_discount


async def calculate_bundle_price(bundle: dict):
    discount = await get_active_discount_for_bundle(bundle)

    return calculate_discounted_price(
        bundle["final_price"],
        discount,
    )