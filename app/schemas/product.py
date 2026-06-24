from enum import Enum
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from datetime import datetime


class ProductType(str, Enum):
    BOOK = "book"
    ACCESSORY = "accessory"


class CoverType(str, Enum):
    PAPERBACK = "paperback"
    HARDCOVER = "hardcover"


class BookDetails(BaseModel):
    author_ids: list[str] = Field(..., min_length=1)
    publisher: str = Field(..., min_length=2, max_length=100)
    isbn: str = Field(..., min_length=10, max_length=17)
    language: str = Field(..., min_length=2, max_length=50)
    pages: int = Field(..., gt=0)
    publication_year: int = Field(..., ge=0)
    cover_type: CoverType


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: str = Field(..., min_length=10, max_length=1000)
    price: Decimal = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)
    category_id: str
    product_type: ProductType
    book_details: BookDetails | None = None

    @model_validator(mode="after")
    def validate_product_details(self):
        if self.product_type == ProductType.BOOK and self.book_details is None:
            raise ValueError("book_details is required for products with type 'book'")

        if self.product_type == ProductType.ACCESSORY and self.book_details is not None:
            raise ValueError("book_details must be empty for products with type 'accessory'")

        return self


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=150)
    description: str | None = Field(None, min_length=10, max_length=1000)
    price: Decimal | None = Field(None, gt=0)
    stock_quantity: int | None = Field(None, ge=0)
    category_id: str | None = None
    book_details: BookDetails | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    price: Decimal
    stock_quantity: int
    category_id: str
    product_type: ProductType
    book_details: BookDetails | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime