from datetime import date

from pydantic import BaseModel, Field


class AuthorCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    biography: str | None = Field(None, max_length=2000)
    country: str | None = Field(None, max_length=100)
    birth_date: date | None = None


class AuthorUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    biography: str | None = Field(None, max_length=2000)
    country: str | None = Field(None, max_length=100)
    birth_date: date | None = None


class AuthorResponse(BaseModel):
    id: str
    name: str
    biography: str | None = None
    country: str | None = None
    birth_date: date | None = None
    is_active: bool