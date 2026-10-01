"""Async client tests (spec 0004)."""

from __future__ import annotations

import httpx
from conftest import (
    LOGIN,
    PASSWORD,
    json_response,
    make_async_client,
    synthetic_session_payload,
)

from pydmvl import password_hash


async def test_async_login_and_fetch() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return json_response(synthetic_session_payload())

    async with make_async_client(handler) as client:
        session = await client.login(LOGIN, PASSWORD)
        fetched = await client.fetch()

    assert session.login == LOGIN
    assert fetched.personal_account.has_debt is True
    assert len(requests) == 2
    for request in requests:
        params = dict(request.url.params)
        assert params["hash"] == password_hash(PASSWORD)
        assert "authorization" not in {key.lower() for key in request.headers}
