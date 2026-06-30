from fastapi import APIRouter, Depends, status

from app.dependencies.auth import require_manager
from app.exceptions.product import ProductNotFoundError
from app.schemas.product import ProductCreate, ProductUpdate, ProductUserResponse, ProductManagerResponse
from app.services.product_service import create_product, get_products, get_active_products, get_product_by_id, update_product, delete_product


router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductManagerResponse, status_code=status.HTTP_201_CREATED)
async def create_product_endpoint(
    product: ProductCreate,
    current_user: dict = Depends(require_manager),
):
    return await create_product(product)


@router.get("/", response_model=list[ProductUserResponse])
async def get_active_products_endpoint():
    return await get_active_products()


@router.get("/manager", response_model=list[ProductManagerResponse])
async def get_products_manager_endpoint(
    current_user: dict = Depends(require_manager),
):
    return await get_products()


@router.get("/manager/{product_id}", response_model=ProductManagerResponse)
async def get_product_manager_endpoint(
    product_id: str,
    current_user: dict = Depends(require_manager),
):
    return await get_product_by_id(product_id)


@router.get("/{product_id}", response_model=ProductUserResponse)
async def get_product_endpoint(product_id: str):
    product = await get_product_by_id(product_id)

    if not product["is_active"]:
        raise ProductNotFoundError

    return product


@router.patch("/{product_id}", response_model=ProductManagerResponse)
async def update_product_endpoint(
    product_id: str,
    product: ProductUpdate,
    current_user: dict = Depends(require_manager),
):
    return await update_product(product_id, product)


@router.delete("/{product_id}", response_model=ProductManagerResponse)
async def delete_product_endpoint(
    product_id: str,
    current_user: dict = Depends(require_manager),
):
    return await delete_product(product_id)