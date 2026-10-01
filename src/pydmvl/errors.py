"""Typed errors raised by the pydmvl client (spec 0004 R4)."""

from __future__ import annotations


class DmvlError(Exception):
    """Base class for all errors raised by pydmvl."""


class AuthError(DmvlError):
    """Authentication failed or was attempted without stored credentials."""


class ApiError(DmvlError):
    """The API returned an unexpected HTTP status or a malformed body.

    Carries the HTTP status of the response that triggered it.
    """

    def __init__(self, message: str, *, status: int) -> None:
        super().__init__(message)
        self.status = status
