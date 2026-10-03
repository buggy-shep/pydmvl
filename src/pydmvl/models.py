"""Parsed account models and pure payload parsers (specs 0002, 0003, 0006-0009).

All parsers are pure and raise ``ValueError``/``KeyError``/``TypeError`` on
malformed input; the client maps those to :class:`~pydmvl.errors.ApiError`
with the HTTP status attached. Amounts are kept as :class:`decimal.Decimal`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

ZERO = Decimal(0)

RECEIPT_KIND_UTILITIES = "utilities"
RECEIPT_KIND_CAPITAL_REPAIR = "capital_repair"


def parse_decimal(value: Any, field: str, *, default: Decimal | None = None) -> Decimal:
    """Parse a JSON number or numeric string into a Decimal.

    Missing or blank values return ``default`` when one is given; otherwise a
    ``ValueError`` is raised. Booleans and non-numeric values are rejected.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        if default is not None:
            return default
        raise ValueError(f"field {field!r} is missing")
    if isinstance(value, bool):
        raise ValueError(f"field {field!r} is not numeric")
    if isinstance(value, (int, float, str)):
        try:
            return Decimal(str(value).strip())
        except InvalidOperation as exc:
            raise ValueError(f"field {field!r} is not numeric") from exc
    raise ValueError(f"field {field!r} is not numeric")


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


_TRUTHY_STRINGS = frozenset({"true", "1"})


def parse_flag(value: Any) -> bool:
    """Coerce a JSON boolean flag to ``bool`` (spec 0009 R3).

    Accepts real booleans, integers (zero is false, any other integer true), and
    the strings ``"true"``/``"1"`` (case-insensitive, trimmed). Any other type
    or value degrades to ``False``, so a malformed flag never flips on.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in _TRUTHY_STRINGS
    return False


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"field {field!r} is not an object")
    return value


def _objects(value: Any) -> list[Any]:
    """Return a list of entries; a missing or non-list value is empty."""
    return value if isinstance(value, list) else []


@dataclass(frozen=True)
class Payment:
    """One payment history entry (spec 0003 R1)."""

    date: str
    amount: Decimal


@dataclass(frozen=True)
class OutstandingPayment:
    """One outstanding amount block entry (spec 0003 R2)."""

    amount: Decimal
    tax: Decimal


@dataclass(frozen=True)
class PaymentSegment:
    """One amount-due segment by payment channel (spec 0008 R1).

    This is the "amount due by channel" breakdown from the ``getpayments``
    action, not a payment history entry (spec 0003). ``provider`` is the
    ``payment_header`` label; ``input`` is the ``payment_input`` amount.
    """

    payment_id: int | None
    provider: str | None
    button: str | None
    amount: Decimal
    tax: Decimal
    tax_amount: Decimal
    input: Decimal


@dataclass(frozen=True)
class PaymentOptions:
    """The ``getpayments`` response: amount-due segments and options (spec 0008)."""

    count: int
    segments: tuple[PaymentSegment, ...]
    text: str | None
    hide_sum_with_tax: bool


@dataclass(frozen=True)
class Charge:
    """One per-period charge (document) (spec 0002 R1)."""

    date: str
    charged: Decimal
    charged_adjusted: Decimal
    benefit: Decimal
    difference: Decimal
    paid: Decimal
    debt_opening: Decimal
    debt_closing: Decimal

    @property
    def is_paid(self) -> bool:
        """Whether the charged amount has been fully paid (spec 0002 R4)."""
        return self.paid >= self.charged


@dataclass(frozen=True)
class Receipt:
    """A receipt link from the snapshot (spec 0002 R3).

    ``link`` is a short-lived URL; consumers must not persist it.
    """

    kind: str
    name: str
    link: str


@dataclass(frozen=True)
class AccountSummary:
    """Aggregates of the personal account (spec 0002 R2)."""

    debt_opening: Decimal
    debt_current: Decimal
    debt_closing: Decimal
    charged: Decimal
    paid: Decimal
    difference: Decimal
    period: str | None
    payment_purpose: str | None
    payments: tuple[Payment, ...]

    @property
    def has_debt(self) -> bool:
        """Whether the current debt is positive (spec 0002 R4)."""
        return self.debt_current > ZERO


@dataclass(frozen=True)
class CounterReading:
    """One meter reading for a period (spec 0006 R2)."""

    period_start: str | None
    period_end: str | None
    reading: Decimal
    volume: Decimal
    kind: str | None
    is_actual: bool


@dataclass(frozen=True)
class Counter:
    """A meter with its reading history (spec 0006 R1).

    Reading is strictly read-only: submitting or deleting a reading is out of
    scope (spec 0006 R4).
    """

    name: str
    serial: str
    service: str | None
    checked: str | None
    readings: tuple[CounterReading, ...]

    @property
    def current_reading(self) -> CounterReading | None:
        """The reading marked actual, or ``None`` when none is (spec 0006 R3)."""
        for reading in self.readings:
            if reading.is_actual:
                return reading
        return None


@dataclass(frozen=True)
class AccountInfo:
    """Account-screen metadata from the authentication response (spec 0007).

    All fields are optional and parsed defensively. ``raw`` is the full parsed
    response body, so callers can reach a field not yet modelled; it contains
    the server-returned ``hash`` and must never be logged or published.
    """

    organization: str | None
    database: str | None
    developer_email: str | None
    contact_email: str | None
    address: str | None
    flat: str | None
    management_key: str | None
    full_name: str | None
    phone: str | None
    contact: Mapping[str, Any] | None
    settings: Mapping[str, Any]
    charges: int
    receipts: int
    counters: int
    payments: int
    news: int
    # Excluded from repr: it holds the server `hash` and other account data.
    raw: Mapping[str, Any] = field(repr=False)


@dataclass(frozen=True)
class Session:
    """The account snapshot returned by the authentication action (spec 0004)."""

    login: str
    name: str | None
    database: str | None
    personal_account: AccountSummary
    charges: tuple[Charge, ...]
    receipts: tuple[Receipt, ...]
    outstanding: tuple[OutstandingPayment, ...]
    counters: tuple[Counter, ...]
    # Excluded from repr: repr(AccountInfo) already excludes the raw payload.
    account: AccountInfo = field(repr=False)

    @property
    def last_payment(self) -> Payment | None:
        """The newest payment history entry, or ``None`` when empty (spec 0003 R3)."""
        return self.personal_account.payments[-1] if self.personal_account.payments else None

    @property
    def has_unpaid_documents(self) -> bool:
        """Whether any document is unpaid (spec 0002 R5)."""
        return self.personal_account.has_debt or any(not charge.is_paid for charge in self.charges)


def parse_payment(entry: Any) -> Payment:
    """Parse one payment history entry from ``fo_date``/``fo_sum``."""
    obj = _object(entry, "payment")
    return Payment(
        date=_optional_str(obj.get("fo_date")) or "",
        amount=parse_decimal(obj.get("fo_sum"), "fo_sum"),
    )


def parse_outstanding_payment(entry: Any) -> OutstandingPayment:
    """Parse one outstanding amount block entry from ``sum``/``tax``."""
    obj = _object(entry, "outstanding payment")
    return OutstandingPayment(
        amount=parse_decimal(obj.get("sum"), "sum", default=ZERO),
        tax=parse_decimal(obj.get("tax"), "tax", default=ZERO),
    )


def parse_payment_segment(entry: Any) -> PaymentSegment:
    """Parse one ``payments[]`` entry of a ``getpayments`` response (spec 0008)."""
    obj = _object(entry, "payment segment")
    return PaymentSegment(
        payment_id=_optional_int(obj.get("payment_id")),
        provider=_optional_str(obj.get("payment_header")),
        button=_optional_str(obj.get("payment_button")),
        amount=parse_decimal(obj.get("payment_sum"), "payment_sum", default=ZERO),
        tax=parse_decimal(obj.get("payment_tax"), "payment_tax", default=ZERO),
        tax_amount=parse_decimal(obj.get("payment_taxsum"), "payment_taxsum", default=ZERO),
        input=parse_decimal(obj.get("payment_input"), "payment_input", default=ZERO),
    )


def parse_payment_options(payload: Any) -> PaymentOptions:
    """Parse a ``getpayments`` response into :class:`PaymentOptions` (spec 0008).

    Parsing is defensive: a missing or non-list ``payments`` value is empty, a
    missing/malformed ``count`` falls back to the number of parsed segments, and
    optional fields degrade to ``None``/``False``/zero. Only a non-object top
    level or a present non-numeric amount raises.
    """
    obj = _object(payload, "payment options")
    segments = tuple(parse_payment_segment(entry) for entry in _objects(obj.get("payments")))
    count = _optional_int(obj.get("count"))
    return PaymentOptions(
        count=count if count is not None else len(segments),
        segments=segments,
        text=_optional_str(obj.get("payment_text")),
        hide_sum_with_tax=obj.get("hideSumWithTax") is True,
    )


def parse_charge(entry: Any) -> Charge:
    """Parse one ``history_charges[]`` entry (spec 0002 R1)."""
    obj = _object(entry, "charge")
    return Charge(
        date=_optional_str(obj.get("ist_date")) or "",
        charged=parse_decimal(obj.get("ist_nach"), "ist_nach", default=ZERO),
        charged_adjusted=parse_decimal(obj.get("ist_nach100"), "ist_nach100", default=ZERO),
        benefit=parse_decimal(obj.get("ist_lgot"), "ist_lgot", default=ZERO),
        difference=parse_decimal(obj.get("ist_raz"), "ist_raz", default=ZERO),
        paid=parse_decimal(obj.get("ist_opl"), "ist_opl", default=ZERO),
        debt_opening=parse_decimal(obj.get("ist_debt_b"), "ist_debt_b", default=ZERO),
        debt_closing=parse_decimal(obj.get("ist_debt_e"), "ist_debt_e", default=ZERO),
    )


def parse_counter_reading(entry: Any) -> CounterReading:
    """Parse one ``values[]`` entry (spec 0006 R2)."""
    obj = _object(entry, "counter reading")
    return CounterReading(
        period_start=_optional_str(obj.get("sp_date_b")),
        period_end=_optional_str(obj.get("sp_date_e")),
        reading=parse_decimal(obj.get("sp_pok"), "sp_pok", default=ZERO),
        volume=parse_decimal(obj.get("sp_val"), "sp_val", default=ZERO),
        kind=_optional_str(obj.get("sp_type")),
        is_actual=parse_flag(obj.get("isActual")),
    )


def parse_counter(entry: Any) -> Counter:
    """Parse one ``counters[]`` entry (spec 0006 R1)."""
    obj = _object(entry, "counter")
    readings = tuple(parse_counter_reading(item) for item in _objects(obj.get("values")))
    return Counter(
        name=_optional_str(obj.get("sch_name")) or "",
        serial=_optional_str(obj.get("sch_id")) or "",
        service=_optional_str(obj.get("st_name")),
        checked=_optional_str(obj.get("sch_date_c")),
        readings=readings,
    )


def _parse_receipts(entries: Any, *, kind: str) -> list[Receipt]:
    receipts: list[Receipt] = []
    for entry in _objects(entries):
        obj = _object(entry, "receipt")
        link = _optional_str(obj.get("link"))
        if not link:
            continue
        receipts.append(Receipt(kind=kind, name=_optional_str(obj.get("name")) or "", link=link))
    return receipts


def parse_account_summary(payload: Any) -> AccountSummary:
    """Parse the ``personal_account`` object (spec 0002 R2)."""
    obj = _object(payload, "personal_account")
    payments = tuple(parse_payment(entry) for entry in _objects(obj.get("payments")))
    return AccountSummary(
        debt_opening=parse_decimal(obj.get("all_debt_b"), "all_debt_b", default=ZERO),
        debt_current=parse_decimal(obj.get("all_debt_c"), "all_debt_c", default=ZERO),
        debt_closing=parse_decimal(obj.get("all_debt_e"), "all_debt_e", default=ZERO),
        charged=parse_decimal(obj.get("all_nach"), "all_nach", default=ZERO),
        paid=parse_decimal(obj.get("all_opl"), "all_opl", default=ZERO),
        difference=parse_decimal(obj.get("all_raz"), "all_raz", default=ZERO),
        period=_optional_str(obj.get("fun_date")),
        payment_purpose=_optional_str(obj.get("textOplUsl")),
        payments=payments,
    )


def parse_account_info(
    payload: Any,
    *,
    charges: tuple[Charge, ...],
    receipts: tuple[Receipt, ...],
    counters: tuple[Counter, ...],
) -> AccountInfo:
    """Parse the account-screen metadata from an authentication payload (0007)."""
    obj = _object(payload, "response")
    raw_settings = obj.get("settings")
    settings = raw_settings if isinstance(raw_settings, dict) else {}
    users = obj.get("usersInfo")
    users_obj = users if isinstance(users, dict) else {}
    contact = obj.get("contact")
    flat = _optional_str(obj.get("mflat"))
    return AccountInfo(
        organization=_optional_str(obj.get("name")),
        database=_optional_str(obj.get("db")),
        developer_email=_optional_str(obj.get("dev_email")),
        contact_email=_optional_str(obj.get("memail")),
        address=_optional_str(obj.get("maddr")),
        flat=flat.strip() if flat else flat,
        management_key=_optional_str(obj.get("mgfkey")),
        full_name=_optional_str(obj.get("fls_fio")),
        phone=_optional_str(users_obj.get("phone")),
        contact=contact if isinstance(contact, dict) else None,
        settings=dict(settings),
        charges=len(charges),
        receipts=len(receipts),
        counters=len(counters),
        payments=len(_objects(obj.get("payments"))),
        news=len(_objects(obj.get("news"))),
        raw=obj,
    )


def parse_session(payload: Any, *, login: str) -> Session:
    """Parse an authentication response body into a :class:`Session`.

    ``login`` is supplied by the caller (the response echoes it back, but the
    caller's value is authoritative).
    """
    obj = _object(payload, "response")
    personal_account = parse_account_summary(obj.get("personal_account"))
    charges = tuple(parse_charge(entry) for entry in _objects(obj.get("history_charges")))
    receipts = [
        *_parse_receipts(obj.get("bills"), kind=RECEIPT_KIND_UTILITIES),
        *_parse_receipts(obj.get("cap_bills"), kind=RECEIPT_KIND_CAPITAL_REPAIR),
    ]
    outstanding = tuple(parse_outstanding_payment(entry) for entry in _objects(obj.get("payments")))
    counters = tuple(parse_counter(entry) for entry in _objects(obj.get("counters")))
    account = parse_account_info(
        payload, charges=charges, receipts=tuple(receipts), counters=counters
    )
    return Session(
        login=login,
        name=_optional_str(obj.get("name")),
        database=_optional_str(obj.get("db")),
        personal_account=personal_account,
        charges=charges,
        receipts=tuple(receipts),
        outstanding=outstanding,
        counters=counters,
        account=account,
    )
