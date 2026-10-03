# 0010 — Unpaid rule and account debt sign

- **Status:** approved
- **Scope:** `pydmvl` derived predicates over the `authentication` snapshot

## Summary

Correct two derived predicates that were documented hypotheses in spec 0002
R4: the sign of the account balance (`all_debt_c`) and the per-period "paid"
test. The payment responses show the balance is a **signed** value where a
negative number means money owed, and that a period is settled against the
**adjusted** charge (`ist_nach100`, i.e. `ist_nach + ist_raz`), not the raw
charge.

## Motivation

`AccountSummary.has_debt` (`debt_current > 0`) returned `False` for an account
that visibly owed money (`all_debt_c < 0`). `Charge.is_paid`
(`paid >= charged`) marked periods unpaid even when the payment fully covered
the charge after a correction (`ist_raz`), inflating the "unpaid" signal.
Both feed `Session.has_unpaid_documents`, the primary signal of the consumer
integration.

## Requirements

- R1 (MUST) `AccountSummary.has_debt` is `debt_current < 0`: the account
  balance is signed, a negative `all_debt_c` means money is owed.
- R2 (MUST) `Charge.is_paid` is `paid >= charged_adjusted`, where
  `charged_adjusted` is `ist_nach100` (the charge adjusted by `ist_raz`).
- R3 (MUST) `Session.has_unpaid_documents` remains
  `personal_account.has_debt or any(charge is not paid)` (spec 0002 R5),
  now built on R1/R2.
- R4 (MUST) Parsing and public field types are unchanged: both are read-only
  properties over already-parsed `Decimal` fields; no new fields are added.
- R5 (SHOULD) `charged_adjusted` is used as-is; when the server omits it, the
  existing zero default applies (no hidden fallback to `charged`), keeping the
  field semantics unambiguous. Consequence: an omitted `ist_nach100` yields
  `paid >= 0` and the period reads as paid; callers that must not lose the
  unpaid signal should rely on the field being present.

## Design

- `models.py`: change the two property bodies; no parsing changes.
- `debt_opening`/`debt_closing` are left untouched (still signed, exposed
  raw); only the derived boolean changes.

## API

No signature changes:

```python
class Charge:
    @property
    def is_paid(self) -> bool: ...  # paid >= charged_adjusted


class AccountSummary:
    @property
    def has_debt(self) -> bool: ...  # debt_current < 0
```

## Test plan

- A charge with a negative correction where `paid == charged_adjusted` is paid
  (regression for R2); one where `paid < charged_adjusted` is not.
- A charge with `paid == charged` but `charged_adjusted > charged` is not paid.
- `has_debt` is `True` for a negative `all_debt_c`, `False` for zero and for a
  positive (overpayment) balance.
- `has_unpaid_documents` combines both predicates.

## Acceptance criteria

- Gate green (`ruff check`, `ruff format --check`, `mypy`, `pytest -m "not
  live"`); the updated predicates are covered by positive and negative cases.

## Out of scope

- States outside the observed range (zero/positive balance): R1 chooses `< 0`
  for "owed", leaving the overpayment semantics as a documented property of the
  sign rather than a separately modelled entity.

## Status

`approved` (2026-10-03) — supersedes the hypothesis clause of spec 0002 R4.
