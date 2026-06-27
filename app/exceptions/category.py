from app.exceptions.base import AppException


class CategoryNotFoundError(AppException):
    status_code = 404
    detail = "Category not found"


class InvalidCategoryIdError(AppException):
    status_code = 404
    detail = "Category not found"


class InvalidParentCategoryError(AppException):
    status_code = 400
    detail = "Invalid parent_id"


class CategorySlugAlreadyExistsError(AppException):
    status_code = 400
    detail = "Category slug already exists"