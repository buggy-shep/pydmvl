"""Credential model and password hashing (spec 0001).

The service authenticates with a login and a password hash passed as request
query parameters. Only the hash is held in memory; the plaintext password is
never stored.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


def password_hash(password: str) -> str:
    """Return the lowercase MD5 hex digest of the UTF-8 password.

    This is the wire format the service expects for the `hash` parameter.
    """
    return hashlib.md5(password.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Credentials:
    """Account credentials held in memory: login plus password hash."""

    login: str
    password_hash: str

    @classmethod
    def from_password(cls, login: str, password: str) -> Credentials:
        """Build credentials from a plaintext password, hashing it once."""
        return cls(login=login, password_hash=password_hash(password))
