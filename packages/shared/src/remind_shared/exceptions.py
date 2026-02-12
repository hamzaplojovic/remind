"""Shared exceptions for Remind."""


class RemindException(Exception):
    """Base exception for all Remind errors."""

    pass


class AuthenticationError(RemindException):
    """Raised when authentication fails."""

    pass


class NotFoundError(RemindException):
    """Raised when a resource is not found."""

    pass


class ValidationError(RemindException):
    """Raised when validation fails."""

    pass


class ConfigError(RemindException):
    """Raised when configuration is invalid."""

    pass


class DatabaseError(RemindException):
    """Raised when a database error occurs."""

    pass


class AIError(RemindException):
    """Raised when AI service error occurs."""

    pass
