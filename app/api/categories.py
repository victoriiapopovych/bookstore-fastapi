from fastapi import APIRouter, Depends, status, HTTPException

from app.dependencies.auth import require_manager
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryUserResponse, CategoryManagerResponse
from app.services.category_service import create_category, get_categories, get_active_categories, get_category_by_id, update_category, delete_category
from app.exceptions.category import CategoryNotFoundError, InvalidCategoryIdError, InvalidParentCategoryError, CategorySlugAlreadyExistsError

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryManagerResponse, status_code=status.HTTP_201_CREATED)
async def create_category_endpoint(
    category: CategoryCreate,
    current_user: dict = Depends(require_manager),
):
    try:
        return await create_category(category)

    except InvalidParentCategoryError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parent_id",
        )

    except CategorySlugAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category slug already exists",
        )


@router.get("/", response_model=list[CategoryUserResponse])
async def get_active_categories_endpoint():
    return await get_active_categories()


@router.get("/manager", response_model=list[CategoryManagerResponse])
async def get_categories_manager_endpoint(
    current_user: dict = Depends(require_manager),
):
    return await get_categories()


@router.get("/manager/{category_id}", response_model=CategoryManagerResponse)
async def get_category_manager_endpoint(
    category_id: str,
    current_user: dict = Depends(require_manager),
):
    try:
        return await get_category_by_id(category_id)

    except InvalidCategoryIdError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )


@router.get("/{category_id}", response_model=CategoryUserResponse)
async def get_category_endpoint(category_id: str):
    try:
        category = await get_category_by_id(category_id)

        if not category["is_active"]:
            raise CategoryNotFoundError

        return category

    except InvalidCategoryIdError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )


@router.patch("/{category_id}", response_model=CategoryManagerResponse)
async def update_category_endpoint(
    category_id: str,
    category: CategoryUpdate,
    current_user: dict = Depends(require_manager),
):
    try:
        return await update_category(category_id, category)

    except InvalidCategoryIdError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    except InvalidParentCategoryError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parent_id",
        )

    except CategorySlugAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category slug already exists",
        )


@router.delete("/{category_id}", response_model=CategoryManagerResponse)
async def delete_category_endpoint(
    category_id: str,
    current_user: dict = Depends(require_manager),
):
    try:
        return await delete_category(category_id)

    except InvalidCategoryIdError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )