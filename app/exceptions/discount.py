from app.exceptions.base import AppException


class DiscountNotFoundError(AppException):
    status_code = 404
    detail = "Discount not found"


class InvalidDiscountIdError(AppException):
    status_code = 404
    detail = "Discount not found"


class InvalidDiscountTargetError(AppException):
    status_code = 400
    detail = "Invalid discount target"


class DiscountOverlapError(AppException):
    status_code = 400
    detail = "Discount period overlaps with existing discount"