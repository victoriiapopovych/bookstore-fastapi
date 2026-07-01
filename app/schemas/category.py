from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CategoryType(str, Enum):
    BOOK = "book"
    ACCESSORY = "accessory"


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=100)
    category_type: CategoryType
    description: str | None = None
    parent_id: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    slug: str | None = Field(None, min_length=2, max_length=100)
    category_type: CategoryType | None = None
    description: str | None = None
    parent_id: str | None = None
    is_active: bool | None = None


class CategoryUserResponse(BaseModel):
    id: str
    name: str
    slug: str
    category_type: CategoryType
    description: str | None = None
    parent_id: str | None = None


class CategoryManagerResponse(CategoryUserResponse):
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PaginatedCategoryUserResponse(BaseModel):
    items: list[CategoryUserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedCategoryManagerResponse(BaseModel):
    items: list[CategoryManagerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int