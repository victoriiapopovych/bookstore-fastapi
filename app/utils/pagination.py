from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


def get_skip(params: PaginationParams) -> int:
    return (params.page - 1) * params.page_size


def build_paginated_response(
    items: list,
    total: int,
    params: PaginationParams,
):
    total_pages = (total + params.page_size - 1) // params.page_size

    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages,
    }