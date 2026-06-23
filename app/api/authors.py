from fastapi import APIRouter, status, HTTPException

from app.schemas.author import AuthorCreate, AuthorResponse, AuthorUpdate
from app.services.author_service import create_author, get_authors, get_author_by_id, update_author, delete_author


router = APIRouter(prefix="/authors", tags=["Authors"])


@router.post("/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author_endpoint(author: AuthorCreate):
    return await create_author(author)


@router.get("/", response_model=list[AuthorResponse])
async def get_authors_endpoint():
    return await get_authors()


@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author_endpoint(author_id: str):
    author = await get_author_by_id(author_id)

    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    return author


@router.patch("/{author_id}", response_model=AuthorResponse)
async def update_author_endpoint(author_id: str, author: AuthorUpdate):
    updated_author = await update_author(author_id, author)

    if not updated_author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    return updated_author


@router.delete("/{author_id}", response_model=AuthorResponse)
async def delete_author_endpoint(author_id: str):
    deleted_author = await delete_author(author_id)

    if not deleted_author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    return deleted_author