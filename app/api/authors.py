from fastapi import APIRouter, Depends, status

from app.dependencies.auth import require_manager
from app.exceptions.author import AuthorNotFoundError
from app.schemas.author import AuthorCreate, AuthorUpdate, AuthorUserResponse, AuthorManagerResponse, PaginatedAuthorManagerResponse, PaginatedAuthorUserResponse
from app.services.author_service import create_author, get_authors, get_active_authors, get_author_by_id, update_author, delete_author

from app.utils.pagination import PaginationParams


router = APIRouter(prefix="/authors", tags=["Authors"])


@router.post("/", response_model=AuthorManagerResponse, status_code=status.HTTP_201_CREATED)
async def create_author_endpoint(
    author: AuthorCreate,
    current_user: dict = Depends(require_manager),
):
    return await create_author(author)


@router.get("/", response_model=PaginatedAuthorUserResponse)
async def get_active_authors_endpoint(
    pagination: PaginationParams = Depends(),
):
    return await get_active_authors(pagination)


@router.get("/manager", response_model=PaginatedAuthorManagerResponse)
async def get_authors_manager_endpoint(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(require_manager),
):
    return await get_authors(pagination)


@router.get("/manager/{author_id}", response_model=AuthorManagerResponse)
async def get_author_manager_endpoint(
    author_id: str,
    current_user: dict = Depends(require_manager),
):
    return await get_author_by_id(author_id)


@router.get("/{author_id}", response_model=AuthorUserResponse)
async def get_author_endpoint(author_id: str):
    author = await get_author_by_id(author_id)

    if not author["is_active"]:
        raise AuthorNotFoundError

    return author


@router.patch("/{author_id}", response_model=AuthorManagerResponse)
async def update_author_endpoint(
    author_id: str,
    author: AuthorUpdate,
    current_user: dict = Depends(require_manager),
):
    return await update_author(author_id, author)


@router.delete("/{author_id}", response_model=AuthorManagerResponse)
async def delete_author_endpoint(
    author_id: str,
    current_user: dict = Depends(require_manager),
):
    return await delete_author(author_id)