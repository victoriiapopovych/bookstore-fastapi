from app.exceptions.base import AppException


class ProductNotFoundError(AppException):
    status_code = 404
    detail = "Product not found"


class InvalidProductIdError(AppException):
    status_code = 404
    detail = "Product not found"


class InvalidProductCategoryError(AppException):
    status_code = 400
    detail = "Invalid category_id"


class InvalidProductAuthorsError(AppException):
    status_code = 400
    detail = "Invalid author_ids"