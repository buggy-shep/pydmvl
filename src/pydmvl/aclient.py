"""Asynchronous client for the homeowner account API (specs 0001, 0004)."""

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
    parse_payment_options_response,
    payment_params,
)
from .auth import Credentials
from .errors import AuthError
from .models import PaymentOptions, Session

LOGGER = logging.getLogger(__name__)


class AsyncDmvlClient:
    """Asynchronous client for the account API (unofficial).

    Mirrors :class:`~pydmvl.client.DmvlClient` and supports ``async with``.
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        version: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        verify: bool | str = DEFAULT_VERIFY,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url, transport=transport, timeout=timeout, verify=verify
        )
        self._version = version
        self._credentials: Credentials | None = None

    async def __aenter__(self) -> AsyncDmvlClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def login(self, login: str, password: str) -> Session:
        """Authenticate and return the account snapshot (spec 0001 R3)."""
        credentials = Credentials.from_password(login, password)
        LOGGER.debug("authenticating account")
        session = await self._authenticate(credentials)
        self._credentials = credentials
        return session

    async def fetch(self) -> Session:
        """Return a fresh account snapshot using the stored credentials."""
        credentials = self._credentials
        if credentials is None:
            raise AuthError("not logged in; call login() first")
        LOGGER.debug("refreshing account snapshot")
        return await self._authenticate(credentials)

    def logout(self) -> None:
        """Forget the stored credentials."""
        self._credentials = None

    async def payment_segments(self) -> PaymentOptions:
        """Return the amount-due segments from ``getpayments`` (spec 0008 R3).

        Requires a prior :meth:`login`; the request is read-only.
        """
        credentials = self._credentials
        if credentials is None:
            raise AuthError("not logged in; call login() first")
        LOGGER.debug("fetching payment segments")
        response = await self._client.get(
            API_PATH,
            params=payment_params(credentials, self._version),
            headers={"Accept": "application/json"},
        )
        return parse_payment_options_response(response)

    async def close(self) -> None:
        """Release the underlying httpx client; idempotent."""
        await self._client.aclose()

    async def _authenticate(self, credentials: Credentials) -> Session:
        response = await self._client.get(
            API_PATH,
            params=auth_params(credentials, self._version),
            headers={"Accept": "application/json"},
        )
        return parse_authentication_response(response, login=credentials.login)
