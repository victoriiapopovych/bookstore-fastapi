from fastapi import APIRouter, status, HTTPException

from app.schemas.discount import DiscountCreate, DiscountResponse, DiscountUpdate
from app.services.discount_service import create_discount, get_discounts, get_discount_by_id, update_discount, delete_discount


router = APIRouter(prefix="/discounts", tags=["Discounts"])


@router.post("/", response_model=DiscountResponse, status_code=status.HTTP_201_CREATED)
async def create_discount_endpoint(discount: DiscountCreate):
    created_discount = await create_discount(discount)

    if not created_discount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid discount target",
        )

    return created_discount


@router.get("/", response_model=list[DiscountResponse])
async def get_discounts_endpoint():
    return await get_discounts()


@router.get("/{discount_id}", response_model=DiscountResponse)
async def get_discount_endpoint(discount_id: str):
    discount = await get_discount_by_id(discount_id)

    if not discount:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discount not found",
        )

    return discount


@router.patch("/{discount_id}", response_model=DiscountResponse)
async def update_discount_endpoint(discount_id: str, discount: DiscountUpdate):
    updated_discount = await update_discount(discount_id, discount)

    if not updated_discount:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discount not found or invalid target",
        )

    return updated_discount


@router.delete("/{discount_id}", response_model=DiscountResponse)
async def delete_discount_endpoint(discount_id: str):
    deleted_discount = await delete_discount(discount_id)

    if not deleted_discount:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discount not found",
        )

    return deleted_discount