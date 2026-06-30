from fastapi import APIRouter, Depends, status

from app.dependencies.auth import require_manager
from app.exceptions.discount import DiscountNotFoundError
from app.schemas.discount import DiscountCreate, DiscountUpdate, DiscountUserResponse, DiscountManagerResponse
from app.services.discount_service import create_discount, get_discounts, get_active_discounts, get_discount_by_id, update_discount, delete_discount


router = APIRouter(prefix="/discounts", tags=["Discounts"])


@router.post("/", response_model=DiscountManagerResponse, status_code=status.HTTP_201_CREATED)
async def create_discount_endpoint(
    discount: DiscountCreate,
    current_user: dict = Depends(require_manager),
):
    return await create_discount(discount)


@router.get("/", response_model=list[DiscountUserResponse])
async def get_active_discounts_endpoint():
    return await get_active_discounts()


@router.get("/manager", response_model=list[DiscountManagerResponse])
async def get_discounts_manager_endpoint(
    current_user: dict = Depends(require_manager),
):
    return await get_discounts()


@router.get("/manager/{discount_id}", response_model=DiscountManagerResponse)
async def get_discount_manager_endpoint(
    discount_id: str,
    current_user: dict = Depends(require_manager),
):
    return await get_discount_by_id(discount_id)


@router.get("/{discount_id}", response_model=DiscountUserResponse)
async def get_discount_endpoint(discount_id: str):
    discount = await get_discount_by_id(discount_id)

    if not discount["is_active"]:
        raise DiscountNotFoundError

    return discount


@router.patch("/{discount_id}", response_model=DiscountManagerResponse)
async def update_discount_endpoint(
    discount_id: str,
    discount: DiscountUpdate,
    current_user: dict = Depends(require_manager),
):
    return await update_discount(discount_id, discount)


@router.delete("/{discount_id}", response_model=DiscountManagerResponse)
async def delete_discount_endpoint(
    discount_id: str,
    current_user: dict = Depends(require_manager),
):
    return await delete_discount(discount_id)