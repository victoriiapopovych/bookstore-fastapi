from pydantic import BaseModel, Field

from datetime import datetime

from enum import Enum


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


class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    category_type: CategoryType
    description: str | None = None
    parent_id: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime