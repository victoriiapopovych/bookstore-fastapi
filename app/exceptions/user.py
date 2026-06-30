from app.exceptions.base import AppException


class UserNotFoundError(AppException):
    status_code = 404
    detail = "User not found"


class InvalidUserIdError(AppException):
    status_code = 404
    detail = "User not found"


class UserEmailAlreadyExistsError(AppException):
    status_code = 400
    detail = "User with this email already exists"


class CannotDeactivateSelfError(AppException):
    status_code = 400
    detail = "Manager cannot deactivate own account"