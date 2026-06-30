from pydantic import BaseModel, Field


class ImportCategoryRequest(BaseModel):
    category_name: str = Field(..., min_length=2)
    category_url: str
    limit: int | None = Field(None, gt=0)


class ImportBookItem(BaseModel):
    category_name: str = Field(..., min_length=2)
    book_url: str


class ImportCustomBooksRequest(BaseModel):
    books: list[ImportBookItem] = Field(..., min_length=1)