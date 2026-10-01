"""Document (charge/receipt/unpaid) tests (spec 0002)."""

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


def test_charges_are_parsed_in_order() -> None:
    session = _client_for(synthetic_session_payload()).login(LOGIN, PASSWORD)
    assert [charge.date for charge in session.charges] == ["09.2026", "10.2026"]
    first = session.charges[0]
    assert first.charged == Decimal("1800.00")
    assert first.paid == Decimal("1800.00")
    assert first.debt_closing == Decimal("100.00")


def test_charge_is_paid_rule() -> None:
    session = _client_for(synthetic_session_payload()).login(LOGIN, PASSWORD)
    assert session.charges[0].is_paid is True
    assert session.charges[1].is_paid is False


def test_account_summary_has_debt_rule() -> None:
    session = _client_for(synthetic_session_payload()).login(LOGIN, PASSWORD)
    summary = session.personal_account
    assert summary.debt_current == Decimal("150.50")
    assert summary.has_debt is True
    assert summary.period == "01.10.2026"
    assert summary.payment_purpose == "for utilities"


def test_has_debt_false_when_no_current_debt() -> None:
    payload = synthetic_session_payload()
    payload["personal_account"]["all_debt_c"] = "0.00"
    session = _client_for(payload).login(LOGIN, PASSWORD)
    assert session.personal_account.has_debt is False


def test_whitespace_amount_defaults_to_zero() -> None:
    payload = synthetic_session_payload()
    payload["history_charges"][0]["ist_lgot"] = "   "
    session = _client_for(payload).login(LOGIN, PASSWORD)
    assert session.charges[0].benefit == Decimal(0)


def test_receipts_include_both_kinds() -> None:
    session = _client_for(synthetic_session_payload()).login(LOGIN, PASSWORD)
    kinds = sorted(receipt.kind for receipt in session.receipts)
    assert kinds == ["capital_repair", "utilities"]
    assert all(receipt.link.startswith("https://") for receipt in session.receipts)


def test_blank_receipt_link_is_skipped() -> None:
    payload = synthetic_session_payload()
    payload["bills"][0]["link"] = ""
    session = _client_for(payload).login(LOGIN, PASSWORD)
    assert [receipt.kind for receipt in session.receipts] == ["capital_repair"]


def test_missing_numeric_fields_default_to_zero() -> None:
    payload = synthetic_session_payload()
    del payload["history_charges"][0]["ist_lgot"]
    session = _client_for(payload).login(LOGIN, PASSWORD)
    assert session.charges[0].benefit == Decimal(0)


def test_has_unpaid_documents_true() -> None:
    session = _client_for(synthetic_session_payload()).login(LOGIN, PASSWORD)
    assert session.has_unpaid_documents is True


def test_has_unpaid_documents_false_when_all_paid() -> None:
    payload = synthetic_session_payload()
    payload["personal_account"]["all_debt_c"] = "0"
    payload["history_charges"][1]["ist_opl"] = "2200.00"
    session = _client_for(payload).login(LOGIN, PASSWORD)
    assert session.has_unpaid_documents is False


def test_malformed_charge_raises_api_error() -> None:
    payload = synthetic_session_payload()
    payload["history_charges"][0]["ist_nach"] = "not-a-number"
    with pytest.raises(ApiError):
        _client_for(payload).login(LOGIN, PASSWORD)
