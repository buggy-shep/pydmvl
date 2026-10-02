"""AccountInfo parsing tests (spec 0007)."""

from __future__ import annotations

from conftest import LOGIN, synthetic_session_payload

from pydmvl import AccountInfo
from pydmvl.models import parse_session


def test_account_info_parses_metadata() -> None:
    session = parse_session(synthetic_session_payload(), login=LOGIN)

    info = session.account
    assert isinstance(info, AccountInfo)
    assert info.organization == "Example account"
    assert info.database == "kp_example"
    assert info.developer_email == "support@example.invalid"
    assert info.contact_email == "resident@example.invalid"
    assert info.address == "Example street, 1"
    assert info.flat == "42"
    assert info.management_key == "<mgfkey>"
    assert info.full_name == "<full name>"
    assert info.phone == "<phone>"
    assert info.settings == {"show_counters": 1, "first_day_counters_values": 15}
    assert info.charges == 2
    assert info.receipts == 2
    assert info.counters == 1
    assert info.payments == 1
    assert info.news == 0


def test_account_info_contact_and_raw() -> None:
    session = parse_session(synthetic_session_payload(), login=LOGIN)

    assert session.account.contact == {"persons": [], "messages": []}
    assert session.account.raw["login"] == LOGIN


def test_account_info_repr_does_not_leak_hash() -> None:
    session = parse_session(synthetic_session_payload(), login=LOGIN)

    assert session.account.raw["hash"]
    assert session.account.raw["hash"] not in repr(session)
    assert session.account.raw["hash"] not in repr(session.account)


def test_account_info_defensive_on_partial_payload() -> None:
    payload = synthetic_session_payload()
    for key in ("settings", "usersInfo", "contact", "maddr", "mflat", "dev_email"):
        payload.pop(key, None)

    info = parse_session(payload, login=LOGIN).account

    assert info.address is None
    assert info.flat is None
    assert info.phone is None
    assert info.contact is None
    assert info.settings == {}
    assert info.charges == 2  # counts still derive from the parsed arrays


def test_account_info_malformed_settings_does_not_raise() -> None:
    payload = synthetic_session_payload()
    payload["settings"] = "oops"

    info = parse_session(payload, login=LOGIN).account

    assert info.settings == {}
