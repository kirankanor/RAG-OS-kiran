from __future__ import annotations


class UserError(Exception):
    """Base exception for all users-domain errors."""


class InvalidEmailError(UserError):
    pass


class WeakPasswordError(UserError):
    pass


class EmailAlreadyRegisteredError(UserError):
    pass


class InvalidCredentialsError(UserError):
    """Deliberately vague: same error for unknown email, wrong password, inactive user."""


class InvalidTokenError(UserError):
    pass


class UserNotFoundError(UserError):
    pass


class OrganizationNotFoundError(UserError):
    pass


class AlreadyInOrganizationError(UserError):
    pass
