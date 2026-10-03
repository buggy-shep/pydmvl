"""Counter reading tests (spec 0006)."""

from __future__ import annotations

from decimal import Decimal

import httpx
from conftest import LOGIN, PASSWORD, json_response, make_client, synthetic_session_payload

from pydmvl import Counter, CounterReading, DmvlClient


def _client_for(payload: dict[str, object]) -> DmvlClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(payload)

    return make_client(handler)


def test_counters_are_parsed_in_order() -> None:
    session = _client_for(synthetic_session_payload()).login(LOGIN, PASSWORD)

    assert len(session.counters) == 1
    counter = session.counters[0]
    assert isinstance(counter, Counter)
    assert counter.name == "<sch_name>"
    assert counter.serial == "<sch_id>"
    assert counter.service == "cold water"
    assert counter.checked == "01.01.2026"
    assert len(counter.readings) == 1


def test_reading_fields_are_parsed() -> None:
    session = _client_for(synthetic_session_payload()).login(LOGIN, PASSWORD)

    reading = session.counters[0].readings[0]
    assert isinstance(reading, CounterReading)
    assert reading.period_start == "01.09.2026"
    assert reading.period_end == "30.09.2026"
    assert reading.reading == Decimal("123")
    assert reading.volume == Decimal("5")
    assert reading.kind == "water"
    assert reading.is_actual is True


def test_current_reading_selects_the_actual_one() -> None:
    payload = synthetic_session_payload()
    payload["counters"][0]["values"].append(
        {
            "sp_date_b": "01.10.2026",
            "sp_date_e": "31.10.2026",
            "sp_pok": "130",
            "sp_val": "7",
            "sp_type": "water",
            "isActual": False,
        }
    )
    session = _client_for(payload).login(LOGIN, PASSWORD)

    current = session.counters[0].current_reading
    assert current is not None
    assert current.reading == Decimal("123")


def test_current_reading_is_none_when_none_actual() -> None:
    payload = synthetic_session_payload()
    payload["counters"][0]["values"][0]["isActual"] = False
    session = _client_for(payload).login(LOGIN, PASSWORD)

    assert session.counters[0].current_reading is None


def test_missing_values_degrade() -> None:
    payload = synthetic_session_payload()
    payload["counters"] = [{"sch_id": "<sch_id>"}]
    session = _client_for(payload).login(LOGIN, PASSWORD)

    counter = session.counters[0]
    assert counter.name == ""
    assert counter.serial == "<sch_id>"
    assert counter.service is None
    assert counter.checked is None
    assert counter.readings == ()
    assert counter.current_reading is None


def test_missing_reading_amounts_degrade_to_zero() -> None:
    payload = synthetic_session_payload()
    reading = payload["counters"][0]["values"][0]
    for key in ("sp_date_b", "sp_date_e", "sp_pok", "sp_val", "sp_type"):
        reading.pop(key, None)
    session = _client_for(payload).login(LOGIN, PASSWORD)

    parsed = session.counters[0].readings[0]
    assert parsed.period_start is None
    assert parsed.period_end is None
    assert parsed.reading == Decimal(0)
    assert parsed.volume == Decimal(0)
    assert parsed.kind is None


def test_missing_counters_array_is_empty() -> None:
    payload = synthetic_session_payload()
    payload.pop("counters", None)
    session = _client_for(payload).login(LOGIN, PASSWORD)

    assert session.counters == ()
    assert session.account.counters == 0
