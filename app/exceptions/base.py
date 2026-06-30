class AppException(Exception):
    status_code = 400
    detail = "Application error"