class RaphaelError(Exception):
    """Base error for Raphael."""


class ValidationError(RaphaelError):
    """Raised when input validation fails."""


class PermissionDeniedError(RaphaelError):
    """Raised when an action is not allowed."""


class NotFoundError(RaphaelError):
    """Raised when a requested item cannot be found."""