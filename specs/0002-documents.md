# 0002 — Documents (charges, receipts, unpaid detection)

- **Status:** approved
- **Scope:** `pydmvl` parsing of the account snapshot returned by
  `authentication`

## Summary

The account snapshot carries per-period charges and receipt links. There is no
separate documents action. This spec defines the charge model, receipt links,
and the derived "unpaid" signal.

## Motivation

The Home Assistant integration's primary purpose is a binary "there are unpaid
documents" signal plus the underlying amounts. Charges and receipts are the
data behind that signal.

## Requirements

- R1 (MUST) Parse `history_charges[]` into `Charge` objects with the fields
  `date` (`ist_date`), `charged` (`ist_nach`), `charged_adjusted`
  (`ist_nach100`), `benefit` (`ist_lgot`), `difference` (`ist_raz`), `paid`
  (`ist_opl`), `debt_opening` (`ist_debt_b`), `debt_closing` (`ist_debt_e`).
  Missing numeric fields default to zero.
- R2 (MUST) Parse `personal_account` into `AccountSummary` with `debt_opening`
  (`all_debt_b`), `debt_current` (`all_debt_c`), `debt_closing` (`all_debt_e`),
  `charged` (`all_nach`), `paid` (`all_opl`), `difference` (`all_raz`),
  `period` (`fun_date`), `payment_purpose` (`textOplUsl`), and the nested
  `payments[]` (spec 0003).
- R3 (MUST) Parse receipt links from `bills[]` and `cap_bills[]` into
  `Receipt(kind, name, link)`, where `kind` is `"utilities"` or
  `"capital_repair"` respectively. A missing `link` is treated as no receipt.
- R4 (MUST) `Charge.is_paid` is `paid >= charged`; `AccountSummary.has_debt` is
  `debt_current > 0`. These are documented hypotheses of the unpaid rule
  (see Notes); they are stable properties, not hard-coded UI logic.
- R5 (MUST) `Session.has_unpaid_documents` is `AccountSummary.has_debt or any
  charge is not paid`.
- R6 (MUST) Amounts are parsed into `decimal.Decimal` from JSON numbers or
  numeric strings; a non-numeric value for a required field raises `ApiError`.
- R7 (SHOULD) Replaceable fields (a periodic charge in progress, an amount left
  blank) degrade to zero rather than failing the whole snapshot.

## Design

- Parsing is pure and lives in `models.py`; the client only maps transport
  errors and attaches the HTTP status.
- Receipt links are exposed as-is; the library never downloads them. They are
  short-lived links and must not be persisted by consumers.

## API

```python
@dataclass(frozen=True)
class Charge:
    date: str
    charged: Decimal
    charged_adjusted: Decimal
    benefit: Decimal
    difference: Decimal
    paid: Decimal
    debt_opening: Decimal
    debt_closing: Decimal

    @property
    def is_paid(self) -> bool: ...


@dataclass(frozen=True)
class Receipt:
    kind: str  # "utilities" | "capital_repair"
    name: str
    link: str


@dataclass(frozen=True)
class AccountSummary:
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
    def has_debt(self) -> bool: ...
```

## Test plan

- Fixture-driven parsing of `history_charges[]`, `personal_account`, `bills[]`,
  and `cap_bills[]`.
- Edge cases: missing numeric fields default to zero; charges with
  `paid >= charged` are paid; a blank link yields no receipt.
- Non-numeric required values raise `ApiError`.

## Acceptance criteria

- Unit tests green; `has_unpaid_documents` and `Charge.is_paid` covered by
  positive and negative cases.

## Notes

- The exact unpaid rule is a hypothesis: a single `debt_closing > 0` is not a
  reliable signal (an observed paid period still carried a closing debt). The
  rule may be refined by a later spec when more states are available.
- `charged_adjusted` (`ist_nach100`) semantics are not fully established; it is
  exposed as a distinct field rather than folded into `charged`.

## Out of scope

- Downloading receipts or rendering PDFs.
- The `getpayments` action (amount-due segments; specified separately in spec
  0008).
- Charges grouped by service (`details_charges[]`).

## Status

`approved` (2026-10-01: gate for the 0.1.0 scope).
