from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class DiscountTargetType(str, Enum):
    PRODUCT = "product"
    CATEGORY = "category"
    BUNDLE = "bundle"


class DiscountCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    discount_type: DiscountType
    value: Decimal = Field(..., gt=0)
    target_type: DiscountTargetType
    target_id: str
    start_date: datetime
    end_date: datetime

    @model_validator(mode="after")
    def validate_discount(self):
        if self.discount_type == DiscountType.PERCENTAGE and self.value > 100:
            raise ValueError("Percentage discount cannot be greater than 100")

        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")

        return self


class DiscountUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=150)
    discount_type: DiscountType | None = None
    value: Decimal | None = Field(None, gt=0)
    target_type: DiscountTargetType | None = None
    target_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_discount(self):
        if self.discount_type == DiscountType.PERCENTAGE and self.value is not None and self.value > 100:
            raise ValueError("Percentage discount cannot be greater than 100")

        if self.start_date is not None and self.end_date is not None:
            if self.end_date <= self.start_date:
                raise ValueError("end_date must be after start_date")

        return self


class DiscountUserResponse(BaseModel):
    id: str
    name: str
    discount_type: DiscountType
    value: Decimal
    target_type: DiscountTargetType
    target_id: str
    start_date: datetime
    end_date: datetime


class DiscountManagerResponse(DiscountUserResponse):
    is_active: bool
    created_at: datetime
    updated_at: datetime