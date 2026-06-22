from fastapi import APIRouter, status, HTTPException

from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import create_category, get_categories, get_category_by_id, update_category, delete_category


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category_endpoint(category: CategoryCreate):
    return await create_category(category)


@router.get("/", response_model=list[CategoryResponse])
async def get_categories_endpoint():
    return await get_categories()


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category_endpoint(category_id: str):
    category = await get_category_by_id(category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category_endpoint(category_id: str, category: CategoryUpdate):
    updated_category = await update_category(category_id, category)

    if not updated_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return updated_category


@router.delete("/{category_id}", response_model=CategoryResponse)
async def delete_category_endpoint(category_id: str):
    deleted_category = await delete_category(category_id)

    if not deleted_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    return deleted_category