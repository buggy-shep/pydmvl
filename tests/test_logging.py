"""Credential redaction tests (spec 0001 R6, spec 0004 R7)."""

from __future__ import annotations

import logging

import httpx
import pytest
from conftest import LOGIN, PASSWORD, json_response, make_client, synthetic_session_payload

from pydmvl import password_hash


def _session_handler(request: httpx.Request) -> httpx.Response:
    return json_response(synthetic_session_payload())


def test_httpx_request_url_is_redacted(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="httpx")
    logging.getLogger("httpx").info(
        "HTTP Request: %s %s",
        "GET",
        httpx.URL(
            "https://example.invalid/api.php?action=authentication&login=secret-login&hash=deadbeef"
        ),
    )
    assert "secret-login" not in caplog.text
    assert "deadbeef" not in caplog.text
    assert "action=authentication" in caplog.text
    assert "login=" in caplog.text
    assert "hash=" in caplog.text


def test_login_does_not_leak_credentials_to_httpx_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    make_client(_session_handler).login(LOGIN, PASSWORD)
    assert PASSWORD not in caplog.text
    assert password_hash(PASSWORD) not in caplog.text
    assert LOGIN not in caplog.text
