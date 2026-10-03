# 0008 — Payment segments (read)

- **Status:** approved
- **Scope:** `pydmvl` read-only support for the `getpayments` action

## Summary

The `getpayments` action returns the **amount due by payment channel**: a list of
segments, each with a provider/channel label, the amount due, its tax, and the
input amount. This spec models those segments (`PaymentSegment`), the wrapping
options object (`PaymentOptions`), and a read-only client method
(`payment_segments()`) on both the synchronous and the asynchronous client.

This is the amount-due breakdown, **not payment history**. The payment history
stays where it already is: `personal_account.payments[]` exposed through
`Session.last_payment` (spec 0003). Each segment carries the same amount due as
the single aggregate in the authentication snapshot; the amounts are duplicated
across channels, not summed, and the number of segments and the tax value can
differ from that aggregate.

## Motivation

The Home Assistant integration exposes an "amount due" sensor and wants the
per-channel breakdown (provider, button, amount, tax) as attributes without
parsing raw JSON itself. The authentication snapshot only carries one aggregate
`payments[]` entry with no channel label and no tax; the `getpayments` action is
the read-only source of the breakdown.

## Requirements

- R1 (MUST) New frozen dataclasses in `models.py`:

  ```python
  @dataclass(frozen=True)
  class PaymentSegment:
      payment_id: int | None  # payment_id
      provider: str | None  # payment_header (channel/provider label)
      button: str | None  # payment_button
      amount: Decimal  # payment_sum
      tax: Decimal  # payment_tax
      tax_amount: Decimal  # payment_taxsum
      input: Decimal  # payment_input


  @dataclass(frozen=True)
  class PaymentOptions:
      count: int  # count, or len(segments) when missing
      segments: tuple[PaymentSegment, ...]
      text: str | None  # payment_text
      hide_sum_with_tax: bool  # hideSumWithTax
  ```

- R2 (MUST) Pure parser `parse_payment_options(payload: Any) -> PaymentOptions`
  in `models.py`, in the same defensive style as the existing parsers:
  - `payments` entries are parsed in order from `payments[]`; a missing or
    non-list `payments` value yields an empty tuple;
  - `count` uses the payload value when it is a non-boolean integer, and falls
    back to `len(segments)` when it is missing or malformed;
  - `text` is `payment_text` or `None`; `hide_sum_with_tax` is true only when
    `hideSumWithTax is True`;
  - numeric fields default to `Decimal(0)` when missing; a non-numeric present
    value raises `ValueError`;
  - `payment_id` is `None` unless it is a non-boolean integer;
  - a non-object top level raises `ValueError`; optional fields never raise.
- R3 (MUST) `DmvlClient.payment_segments() -> PaymentOptions` (sync,
  `client.py`) and `AsyncDmvlClient.payment_segments()` (async, `aclient.py`):
  - require a prior `login()`; otherwise raise
    `AuthError("not logged in; call login() first")`, exactly as `fetch()`;
  - call `GET API_PATH` with `action=getpayments`, the stored `login` and
    `hash`, and `version` when the client was configured with one;
  - a non-200 response raises `ApiError` carrying `.status`;
  - a malformed (non-JSON) body raises `ApiError`;
  - a payload with a truthy `error` raises `AuthError`;
  - a malformed parsed payload raises `ApiError`;
  - the method is strictly read-only: it does not create, submit, or mutate
    anything.
- R4 (MUST) Credentials, the password hash, and request URLs are never logged.
  The method reuses the existing `httpx` redaction filter, which already covers
  `login`/`hash` for every request URL (spec 0004 R7); the new request adds no
  logging of its own beyond a debug-level, data-free message.
- R5 (MUST) `PaymentSegment` and `PaymentOptions` are exported from the package
  root and listed in `__all__`.
- R6 (SHOULD) The mapper (`parse_payment_options_response`) lives in `_api.py`
  alongside `parse_authentication_response`, so the sync and async clients share
  identical mapping and error semantics.

## Design

- `models.py` holds `PaymentSegment`, `PaymentOptions`, and the pure
  `parse_payment_options`; `_api.py` adds `ACTION_GETPAYMENTS`, a
  `payment_params(credentials, version)` builder mirroring `auth_params`, and
  the `parse_payment_options_response(response)` mapper, which owns the
  HTTP-status, malformed-body, and `error`-payload handling.
- Both clients follow the existing `fetch()` shape: read stored credentials,
  raise `AuthError` when absent, issue one GET, delegate to the shared mapper.
- `count` is taken from the payload when valid and otherwise derived from the
  parsed segments; the two can legitimately differ in the observed payload, so
  the payload value is authoritative and the derived value is only a fallback.
- Amounts are `Decimal`, never `float`, matching the rest of the library.

## API

```python
from decimal import Decimal

from pydmvl import DmvlClient, PaymentOptions, PaymentSegment

client = DmvlClient()
client.login("user", "secret")
options: PaymentOptions = client.payment_segments()
for segment in options.segments:
    assert isinstance(segment.amount, Decimal)
client.close()
```

```python
async with AsyncDmvlClient() as client:
    await client.login("user", "secret")
    options = await client.payment_segments()
```

## Test plan

- Fixture-driven parsing of a synthetic `getpayments` payload with two segments:
  every field, the `Decimal` amounts, `count`, `text`, and `hide_sum_with_tax`.
- Defensive parsing: missing `payments`/`count`/`payment_text`, missing numeric
  fields (degrade to zero/`None`/`False`), and a non-integer `payment_id`.
- A payload without `count` falls back to `len(segments)`.
- Sync and async `payment_segments()` require a prior `login()` (`AuthError`).
- Request shape: `action=getpayments` plus `login`/`hash` (and `version` when
  configured); no `Authorization` header.
- Error mapping: non-200 (`ApiError.status`), malformed body (`ApiError`),
  `error` payload (`AuthError`).
- Credential redaction covers the new request path.

## Acceptance criteria

- Gate green (`ruff check`, `ruff format --check`, `mypy`, `pytest -m "not
  live"`); the new code paths are covered by tests; a skeptic review returns no
  `BLOCKING` findings; version bumped to 0.4.0.

## Out of scope

- Payment history (already covered by spec 0003).
- Creating a payment link or QR code (`addpayment`) and any writing action.
- Resolving `payment_id` into a payment flow; the field is exposed as read data
  only.

## Status

`approved` (2026-10-03: gate for the 0.4.0 payment-segments scope).
