"""Authentication tests (spec 0001)."""

from __future__ import annotations

import hashlib
import logging

import httpx
import pytest
from conftest import (
    LOGIN,
    PASSWORD,
    json_response,
    load_fixture,
    make_client,
    synthetic_session_payload,
)

from pydmvl import ApiError, AuthError, Credentials, password_hash


def _session_handler(request: httpx.Request) -> httpx.Response:
    return json_response(synthetic_session_payload())


def test_password_hash_matches_md5() -> None:
    assert password_hash(PASSWORD) == hashlib.md5(PASSWORD.encode("utf-8")).hexdigest()


def test_credentials_do_not_keep_plaintext() -> None:
    credentials = Credentials.from_password(LOGIN, PASSWORD)
    assert credentials.login == LOGIN
    assert credentials.password_hash == password_hash(PASSWORD)
    assert PASSWORD not in repr(credentials)


def test_login_sends_query_auth_params() -> None:
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return json_response(synthetic_session_payload())

    session = make_client(handler).login(LOGIN, PASSWORD)

    request = captured["request"]
    params = dict(request.url.params)
    assert params["action"] == "authentication"
    assert params["login"] == LOGIN
    assert params["hash"] == password_hash(PASSWORD)
    assert "version" not in params
    assert "authorization" not in {key.lower() for key in request.headers}
    assert request.headers["accept"] == "application/json"
    assert session.login == LOGIN


def test_login_sends_configured_version() -> None:
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return json_response(synthetic_session_payload())

    make_client(handler, version="1.2.3").login(LOGIN, PASSWORD)
    assert dict(captured["request"].url.params)["version"] == "1.2.3"


def test_password_hash_is_not_logged(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="pydmvl")
    make_client(_session_handler).login(LOGIN, PASSWORD)
    assert PASSWORD not in caplog.text
    assert password_hash(PASSWORD) not in caplog.text


def test_fetch_without_login_raises_auth_error() -> None:
    client = make_client(_session_handler)
    with pytest.raises(AuthError):
        client.fetch()


def test_logout_clears_credentials() -> None:
    client = make_client(_session_handler)
    client.login(LOGIN, PASSWORD)
    client.logout()
    with pytest.raises(AuthError):
        client.fetch()


def test_rejected_login_raises_auth_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(load_fixture("authentication_error.json"))

    with pytest.raises(AuthError):
        make_client(handler).login(LOGIN, PASSWORD)


def test_non_200_raises_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=500, text="boom")

    with pytest.raises(ApiError) as excinfo:
        make_client(handler).login(LOGIN, PASSWORD)
    assert excinfo.value.status == 500
    assert "hash" not in str(excinfo.value)


def test_malformed_body_raises_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, text="not json")

    with pytest.raises(ApiError):
        make_client(handler).login(LOGIN, PASSWORD)


def test_missing_personal_account_raises_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response({"name": "Example account"})

    with pytest.raises(ApiError):
        make_client(handler).login(LOGIN, PASSWORD)
