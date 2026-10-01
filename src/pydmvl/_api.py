"""Internal transport-agnostic API helpers shared by the sync and async clients.

Constants here are observed protocol values of the public service and are
functionally required for the client to work.
"""

from __future__ import annotations

from typing import Any

import httpx

from ._logging import install_httpx_redaction
from .auth import Credentials
from .errors import ApiError, AuthError
from .models import Session, parse_session

install_httpx_redaction()

DEFAULT_BASE_URL = "https://houseb.ru/api/"
API_PATH = "api.php"
ACTION_AUTHENTICATION = "authentication"
DEFAULT_TIMEOUT_SECONDS = 30.0


def auth_params(credentials: Credentials, version: str | None) -> dict[str, str]:
    """Build the query parameters for the authentication action (spec 0001)."""
    params = {
        "action": ACTION_AUTHENTICATION,
        "login": credentials.login,
        "hash": credentials.password_hash,
    }
    if version is not None:
        params["version"] = version
    return params


def parse_authentication_response(response: httpx.Response, *, login: str) -> Session:
    """Map an authentication response to a :class:`Session` (spec 0001 R7)."""
    if response.status_code != 200:
        raise ApiError(
            f"authentication returned HTTP {response.status_code}",
            status=response.status_code,
        )
    try:
        payload: Any = response.json()
    except ValueError as exc:
        raise ApiError(
            "authentication returned a malformed body", status=response.status_code
        ) from exc
    if isinstance(payload, dict) and payload.get("error"):
        raise AuthError("authentication was rejected")
    try:
        return parse_session(payload, login=login)
    except (KeyError, TypeError, ValueError) as exc:
        raise ApiError(f"malformed session payload: {exc}", status=response.status_code) from exc
