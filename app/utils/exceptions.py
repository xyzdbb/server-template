class AppException(Exception):
    """Base application exception"""
    status_code: int = 400

    def __init__(self, detail: str = "Application error"):
        self.detail = detail
        super().__init__(detail)

class DatabaseException(AppException):
    """Database related exception"""
    status_code = 503

class AuthException(AppException):
    """Authentication exception"""
    status_code = 401

class NotFoundException(AppException):
    """Resource not found exception"""
    status_code = 404


class ValidationException(AppException):
    """Validation exception"""
    status_code = 400


class ConflictException(AppException):
    """Conflict exception"""
    status_code = 409


class PermissionDeniedException(AppException):
    """Permission denied exception"""
    status_code = 403