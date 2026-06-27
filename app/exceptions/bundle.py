from app.exceptions.base import AppException


class BundleNotFoundError(AppException):
    status_code = 404
    detail = "Bundle not found"


class InvalidBundleIdError(AppException):
    status_code = 404
    detail = "Bundle not found"


class InvalidBundleProductsError(AppException):
    status_code = 400
    detail = "Invalid product_ids"