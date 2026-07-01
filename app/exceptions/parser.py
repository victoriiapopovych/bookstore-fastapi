from app.exceptions.base import AppException


class ParserError(AppException):
    status_code = 400
    detail = "Parser error"


class ExternalSiteUnavailableError(AppException):
    status_code = 503
    detail = "External book site is unavailable"


class ExternalPageNotFoundError(AppException):
    status_code = 404
    detail = "External page not found"


class InvalidParserUrlError(AppException):
    status_code = 400
    detail = "Invalid parser URL"


class BookImportFailedError(AppException):
    status_code = 400
    detail = "Book import failed"


class NoBooksFoundError(AppException):
    status_code = 404
    detail = "No books found for this category"