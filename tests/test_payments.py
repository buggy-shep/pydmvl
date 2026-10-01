"""Payment tests (spec 0003)."""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
from conftest import LOGIN, PASSWORD, json_response, make_client, synthetic_session_payload

from pydmvl import ApiError, DmvlClient


def _client_for(payload: dict[str, object]) -> DmvlClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(payload)

    return make_client(handler)


def test_payment_history_is_parsed_in_order() -> None:
    session = _client_for(synthetic_session_payload()).login(LOGIN, PASSWORD)
    payments = session.personal_account.payments
    assert [payment.date for payment in payments] == ["05.09.2026", "10.10.2026"]
    assert payments[1].amount == Decimal("1849.50")


def test_last_payment_is_newest_entry() -> None:
    session = _client_for(synthetic_session_payload()).login(LOGIN, PASSWORD)
    last = session.last_payment
    assert last is not None
    assert last.date == "10.10.2026"
    assert last.amount == Decimal("1849.50")


def test_last_payment_none_when_history_empty() -> None:
    payload = synthetic_session_payload()
    payload["personal_account"]["payments"] = []
    session = _client_for(payload).login(LOGIN, PASSWORD)
    assert session.last_payment is None


def test_outstanding_payments_parsed() -> None:
    session = _client_for(synthetic_session_payload()).login(LOGIN, PASSWORD)
    assert len(session.outstanding) == 1
    assert session.outstanding[0].amount == Decimal("2200.00")
    assert session.outstanding[0].tax == Decimal(0)


def test_outstanding_missing_tax_defaults_to_zero() -> None:
    payload = synthetic_session_payload()
    del payload["payments"][0]["tax"]
    session = _client_for(payload).login(LOGIN, PASSWORD)
    assert session.outstanding[0].tax == Decimal(0)


def test_non_numeric_payment_amount_raises_api_error() -> None:
    payload = synthetic_session_payload()
    payload["personal_account"]["payments"][0]["fo_sum"] = "not-a-number"
    with pytest.raises(ApiError):
        _client_for(payload).login(LOGIN, PASSWORD)
