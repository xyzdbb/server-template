class AppException(Exception):
    """Base application exception"""
    pass

class DatabaseException(AppException):
    """Database related exception"""
    pass

class AuthException(AppException):
    """Authentication exception"""
    pass

class NotFoundException(AppException):
    """Resource not found exception"""
    pass