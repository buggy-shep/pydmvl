"""Synchronous client for the homeowner account API (specs 0001, 0004)."""

from __future__ import annotations

import logging

import httpx

from ._api import (
    API_PATH,
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_VERIFY,
    auth_params,
    parse_authentication_response,
)
from .auth import Credentials
from .errors import AuthError
from .models import Session

LOGGER = logging.getLogger(__name__)


class DmvlClient:
    """Synchronous client for the account API (unofficial).

    Credentials are held in memory only; the plaintext password is never
    stored. The transport is injectable for tests (``httpx.MockTransport``).
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        version: str | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        verify: bool | str = DEFAULT_VERIFY,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url, transport=transport, timeout=timeout, verify=verify
        )
        self._version = version
        self._credentials: Credentials | None = None

    def __enter__(self) -> DmvlClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def login(self, login: str, password: str) -> Session:
        """Authenticate and return the account snapshot (spec 0001 R3)."""
        credentials = Credentials.from_password(login, password)
        LOGGER.debug("authenticating account")
        session = self._authenticate(credentials)
        self._credentials = credentials
        return session

    def fetch(self) -> Session:
        """Return a fresh account snapshot using the stored credentials."""
        credentials = self._credentials
        if credentials is None:
            raise AuthError("not logged in; call login() first")
        LOGGER.debug("refreshing account snapshot")
        return self._authenticate(credentials)

    def logout(self) -> None:
        """Forget the stored credentials."""
        self._credentials = None

    def close(self) -> None:
        """Release the underlying httpx client; idempotent."""
        self._client.close()

    def _authenticate(self, credentials: Credentials) -> Session:
        response = self._client.get(
            API_PATH,
            params=auth_params(credentials, self._version),
            headers={"Accept": "application/json"},
        )
        return parse_authentication_response(response, login=credentials.login)
