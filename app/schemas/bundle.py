from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


class BundleItem(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)


class BundleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: str = Field(..., min_length=10, max_length=1000)
    items: list[BundleItem] = Field(..., min_length=1)
    discount_percent: int = Field(..., ge=0, le=100)


class BundleUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=150)
    description: str | None = Field(None, min_length=10, max_length=1000)
    items: list[BundleItem] = Field(..., min_length=1)
    discount_percent: int | None = Field(None, ge=0, le=100)
    is_active: bool | None = None


class BundleResponse(BaseModel):
    id: str
    name: str
    description: str
    items: list[BundleItem] = Field(..., min_length=1)
    discount_percent: int
    original_price: Decimal
    final_price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime