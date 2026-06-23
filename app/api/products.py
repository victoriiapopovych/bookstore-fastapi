from fastapi import APIRouter, status, HTTPException

from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import create_product, get_products, get_product_by_id, update_product, delete_product


router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product_endpoint(product: ProductCreate):
    created_product = await create_product(product)

    if not created_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category_id or author_ids",
        )

    return created_product


@router.get("/", response_model=list[ProductResponse])
async def get_products_endpoint():
    return await get_products()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_endpoint(product_id: str):
    product = await get_product_by_id(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product_endpoint(product_id: str, product: ProductUpdate):
    updated_product = await update_product(product_id, product)

    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or invalid category_id",
        )

    return updated_product


@router.delete("/{product_id}", response_model=ProductResponse)
async def delete_product_endpoint(product_id: str):
    deleted_product = await delete_product(product_id)

    if not deleted_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return deleted_product