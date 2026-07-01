from fastapi import APIRouter, Depends, status

from app.dependencies.auth import require_manager
from app.exceptions.category import CategoryNotFoundError
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryUserResponse, CategoryManagerResponse, PaginatedCategoryManagerResponse, PaginatedCategoryUserResponse
from app.services.category_service import create_category, get_categories, get_active_categories, get_category_by_id, update_category, delete_category

from app.utils.pagination import PaginationParams


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryManagerResponse, status_code=status.HTTP_201_CREATED)
async def create_category_endpoint(
    category: CategoryCreate,
    current_user: dict = Depends(require_manager),
):
    return await create_category(category)


@router.get("/", response_model=PaginatedCategoryUserResponse)
async def get_active_categories_endpoint(
    pagination: PaginationParams = Depends(),
):
    return await get_active_categories(pagination)


@router.get("/manager", response_model=PaginatedCategoryManagerResponse)
async def get_categories_manager_endpoint(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(require_manager),
):
    return await get_categories(pagination)


@router.get("/manager/{category_id}", response_model=CategoryManagerResponse)
async def get_category_manager_endpoint(
    category_id: str,
    current_user: dict = Depends(require_manager),
):
    return await get_category_by_id(category_id)


@router.get("/{category_id}", response_model=CategoryUserResponse)
async def get_category_endpoint(category_id: str):
    category = await get_category_by_id(category_id)

    if not category["is_active"]:
        raise CategoryNotFoundError

    return category


@router.patch("/{category_id}", response_model=CategoryManagerResponse)
async def update_category_endpoint(
    category_id: str,
    category: CategoryUpdate,
    current_user: dict = Depends(require_manager),
):
    return await update_category(category_id, category)


@router.delete("/{category_id}", response_model=CategoryManagerResponse)
async def delete_category_endpoint(
    category_id: str,
    current_user: dict = Depends(require_manager),
):
    return await delete_category(category_id)