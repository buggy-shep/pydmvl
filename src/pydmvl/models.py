"""Parsed account models and pure payload parsers (specs 0002, 0003).

All parsers are pure and raise ``ValueError``/``KeyError``/``TypeError`` on
malformed input; the client maps those to :class:`~pydmvl.errors.ApiError`
with the HTTP status attached. Amounts are kept as :class:`decimal.Decimal`.
"""

from __future__ import annotations

from dataclasses import dataclass
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
class Session:
    """The account snapshot returned by the authentication action (spec 0004)."""

    login: str
    name: str | None
    database: str | None
    personal_account: AccountSummary
    charges: tuple[Charge, ...]
    receipts: tuple[Receipt, ...]
    outstanding: tuple[OutstandingPayment, ...]

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
    return Session(
        login=login,
        name=_optional_str(obj.get("name")),
        database=_optional_str(obj.get("db")),
        personal_account=personal_account,
        charges=charges,
        receipts=tuple(receipts),
        outstanding=outstanding,
    )
