"""Client lifecycle and request shape tests (spec 0004)."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from conftest import LOGIN, PASSWORD, json_response, make_client, synthetic_session_payload

from pydmvl import AuthError, password_hash


def _recording_handler() -> tuple[list[httpx.Request], Callable[[httpx.Request], httpx.Response]]:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return json_response(synthetic_session_payload())

    return requests, handler


def test_login_then_fetch_reuses_credentials() -> None:
    requests, handler = _recording_handler()
    client = make_client(handler)
    client.login(LOGIN, PASSWORD)
    client.fetch()

    assert len(requests) == 2
    for request in requests:
        params = dict(request.url.params)
        assert params["login"] == LOGIN
        assert params["hash"] == password_hash(PASSWORD)


def test_context_manager_closes_client() -> None:
    requests, handler = _recording_handler()
    with make_client(handler) as client:
        client.login(LOGIN, PASSWORD)
    assert len(requests) == 1


def test_close_is_idempotent() -> None:
    _, handler = _recording_handler()
    client = make_client(handler)
    client.close()
    client.close()


def test_fetch_after_logout_raises() -> None:
    _, handler = _recording_handler()
    client = make_client(handler)
    client.login(LOGIN, PASSWORD)
    client.logout()
    with pytest.raises(AuthError):
        client.fetch()
