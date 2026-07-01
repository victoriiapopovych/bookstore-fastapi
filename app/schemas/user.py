from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    CUSTOMER = "customer"
    MANAGER = "manager"


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=2, max_length=50)
    last_name: str | None = Field(None, min_length=2, max_length=50)
    password: str | None = Field(None, min_length=8, max_length=72)


class UserSelfResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    created_at: datetime
    updated_at: datetime


class UserManagerResponse(UserSelfResponse):
    is_active: bool


class PaginatedUserManagerResponse(BaseModel):
    items: list[UserManagerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int