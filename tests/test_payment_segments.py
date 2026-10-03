"""Payment segment tests (spec 0008)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import httpx
import pytest
from conftest import (
    LOGIN,
    PASSWORD,
    json_response,
    load_fixture,
    make_async_client,
    make_client,
    synthetic_session_payload,
)

from pydmvl import (
    ApiError,
    AuthError,
    PaymentOptions,
    PaymentSegment,
    password_hash,
)
from pydmvl.models import parse_payment_options


def _options_payload() -> dict[str, Any]:
    return load_fixture("payment_options.json")


def _dispatching_handler(
    options_payload: Any,
    *,
    status: int = 200,
    raw_text: str | None = None,
) -> tuple[list[httpx.Request], Callable[[httpx.Request], httpx.Response]]:
    """Serve the authentication fixture for login and ``options_payload`` otherwise."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.params.get("action") == "getpayments":
            if raw_text is not None:
                return httpx.Response(status_code=status, text=raw_text)
            return json_response(options_payload, status=status)
        return json_response(synthetic_session_payload())

    return requests, handler


def test_parse_payment_options_fields() -> None:
    options = parse_payment_options(_options_payload())

    assert isinstance(options, PaymentOptions)
    assert options.count == 2
    assert options.text == "<payment text>"
    assert options.hide_sum_with_tax is True
    assert len(options.segments) == 2

    first = options.segments[0]
    assert isinstance(first, PaymentSegment)
    assert first.payment_id == 101
    assert first.provider == "<provider>"
    assert first.button == "Pay"
    assert first.amount == Decimal("1250.75")
    assert first.tax == Decimal(0)
    assert first.tax_amount == Decimal(0)
    assert first.input == Decimal(0)

    second = options.segments[1]
    assert second.payment_id == 202
    assert second.provider == "<provider two>"
    assert second.tax == Decimal(1)
    assert second.tax_amount == Decimal("12.5")
    assert second.input == Decimal(1250)


def test_parse_payment_options_missing_count_falls_back() -> None:
    payload = _options_payload()
    payload.pop("count")

    options = parse_payment_options(payload)

    assert options.count == len(options.segments) == 2


def test_parse_payment_options_payload_count_is_authoritative() -> None:
    payload = _options_payload()
    payload["count"] = 5

    options = parse_payment_options(payload)

    assert options.count == 5
    assert len(options.segments) == 2


@pytest.mark.parametrize("bad_count", [True, "2", 2.5, None])
def test_parse_payment_options_malformed_count_falls_back(bad_count: Any) -> None:
    payload = _options_payload()
    payload["count"] = bad_count

    options = parse_payment_options(payload)

    assert options.count == len(options.segments) == 2


def test_parse_payment_options_hide_sum_with_tax_is_strict() -> None:
    payload = _options_payload()
    payload["hideSumWithTax"] = 1

    assert parse_payment_options(payload).hide_sum_with_tax is False


def test_parse_payment_options_defensive() -> None:
    payload = {
        "payments": [
            {"payment_id": "<not an int>"},
        ]
    }

    options = parse_payment_options(payload)

    assert options.count == 1
    assert options.text is None
    assert options.hide_sum_with_tax is False
    segment = options.segments[0]
    assert segment.payment_id is None
    assert segment.provider is None
    assert segment.button is None
    assert segment.amount == Decimal(0)
    assert segment.tax == Decimal(0)
    assert segment.tax_amount == Decimal(0)
    assert segment.input == Decimal(0)


def test_parse_payment_options_missing_payments_is_empty() -> None:
    options = parse_payment_options({})

    assert options.count == 0
    assert options.segments == ()


def test_parse_payment_options_malformed_top_level_raises() -> None:
    with pytest.raises(ValueError):
        parse_payment_options(["not", "an", "object"])


def test_parse_payment_options_present_non_numeric_raises() -> None:
    payload = {"payments": [{"payment_id": 1, "payment_sum": "oops"}]}

    with pytest.raises(ValueError):
        parse_payment_options(payload)


def test_payment_segments_returns_options() -> None:
    _, handler = _dispatching_handler(_options_payload())
    client = make_client(handler)
    client.login(LOGIN, PASSWORD)

    options = client.payment_segments()

    assert isinstance(options, PaymentOptions)
    assert options.count == 2
    assert options.segments[1].provider == "<provider two>"


def test_payment_segments_request_shape() -> None:
    requests, handler = _dispatching_handler(_options_payload())
    client = make_client(handler, version="9.9.9")
    client.login(LOGIN, PASSWORD)

    client.payment_segments()

    request = requests[-1]
    params = dict(request.url.params)
    assert params["action"] == "getpayments"
    assert params["login"] == LOGIN
    assert params["hash"] == password_hash(PASSWORD)
    assert params["version"] == "9.9.9"
    assert "authorization" not in {key.lower() for key in request.headers}


def test_payment_segments_requires_login() -> None:
    _, handler = _dispatching_handler(_options_payload())
    client = make_client(handler)

    with pytest.raises(AuthError, match="not logged in"):
        client.payment_segments()


def test_payment_segments_after_logout_raises() -> None:
    _, handler = _dispatching_handler(_options_payload())
    client = make_client(handler)
    client.login(LOGIN, PASSWORD)
    client.logout()

    with pytest.raises(AuthError, match="not logged in"):
        client.payment_segments()


def test_payment_segments_non_200_raises_api_error_with_status() -> None:
    _, handler = _dispatching_handler({"error": True}, status=500)
    client = make_client(handler)
    client.login(LOGIN, PASSWORD)

    with pytest.raises(ApiError) as excinfo:
        client.payment_segments()

    assert excinfo.value.status == 500


def test_payment_segments_malformed_body_raises_api_error() -> None:
    _, handler = _dispatching_handler(None, raw_text="<html>not json</html>")
    client = make_client(handler)
    client.login(LOGIN, PASSWORD)

    with pytest.raises(ApiError) as excinfo:
        client.payment_segments()

    assert excinfo.value.status == 200


def test_payment_segments_error_payload_raises_auth_error() -> None:
    _, handler = _dispatching_handler({"error": "session expired"})
    client = make_client(handler)
    client.login(LOGIN, PASSWORD)

    with pytest.raises(AuthError):
        client.payment_segments()


def test_payment_segments_does_not_leak_credentials(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    _, handler = _dispatching_handler(_options_payload())
    client = make_client(handler)
    client.login(LOGIN, PASSWORD)

    client.payment_segments()

    assert PASSWORD not in caplog.text
    assert password_hash(PASSWORD) not in caplog.text
    assert LOGIN not in caplog.text


async def test_async_payment_segments_returns_options() -> None:
    _, handler = _dispatching_handler(_options_payload())

    async def async_handler(request: httpx.Request) -> httpx.Response:
        return handler(request)

    async with make_async_client(async_handler) as client:
        await client.login(LOGIN, PASSWORD)
        options = await client.payment_segments()

    assert isinstance(options, PaymentOptions)
    assert options.segments[0].payment_id == 101


async def test_async_payment_segments_requires_login() -> None:
    _, handler = _dispatching_handler(_options_payload())

    async def async_handler(request: httpx.Request) -> httpx.Response:
        return handler(request)

    async with make_async_client(async_handler) as client:
        with pytest.raises(AuthError, match="not logged in"):
            await client.payment_segments()
