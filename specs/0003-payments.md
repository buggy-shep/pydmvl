# 0003 — Payments

- **Status:** approved
- **Scope:** `pydmvl` payment history and the outstanding amount block

## Summary

The account snapshot carries a payment history under the personal account and a
top-level outstanding-amount block. This spec defines both models and the
latest-payment helper.

## Motivation

The Home Assistant integration exposes "last payment" (date and amount) as a
sensor. The outstanding block supports the unpaid indicator from spec 0002.

## Requirements

- R1 (MUST) Parse `personal_account.payments[]` into `Payment(date, amount)`
  from `fo_date` and `fo_sum`, preserving order.
- R2 (MUST) Parse the top-level `payments[]` into `OutstandingPayment(amount,
  tax)` from `sum` and `tax`; missing `tax` defaults to zero.
- R3 (MUST) `Session.last_payment` returns the newest `Payment` (the last
  element of the history) or `None` when the history is empty.
- R4 (MUST) Non-numeric `fo_sum`/`sum` for a present entry raises `ApiError`.
- R5 (SHOULD) A non-list `payments` value is treated as an empty tuple.

## Design

- Order in the history is taken as given; the library does not sort by date
  (dates are locale-formatted strings of unknown format).
- Payment history comes only from the snapshot
  (`personal_account.payments[]`). The `getpayments` action returns the
  "amount due by channel" breakdown, not history, and is specified separately in
  spec 0008.

## API

```python
@dataclass(frozen=True)
class Payment:
    date: str
    amount: Decimal


@dataclass(frozen=True)
class OutstandingPayment:
    amount: Decimal
    tax: Decimal


class Session:
    @property
    def last_payment(self) -> Payment | None: ...
```

## Test plan

- Fixture-driven parsing of a multi-entry history; `last_payment` returns the
  last entry and `None` for an empty history.
- Missing `tax` defaults to zero; non-numeric `fo_sum` raises `ApiError`.

## Acceptance criteria

- Unit tests green; `last_payment` covered for non-empty and empty histories.

## Out of scope

- Creating payment links (`addpayment`) and payment providers.
- Payment statuses (the payload exposes no status field).
- The `getpayments` amount-due segments (spec 0008); this spec covers payment
  history only.

## Status

`approved` (2026-10-01: gate for the 0.1.0 scope).
