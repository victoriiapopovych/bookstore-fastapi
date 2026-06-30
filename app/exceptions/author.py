from app.exceptions.base import AppException


class AuthorNotFoundError(AppException):
    status_code = 404
    detail = "Author not found"


class InvalidAuthorIdError(AppException):
    status_code = 404
    detail = "Author not found"