# 0007 — Account info (raw account metadata)

- **Status:** implemented
- **Scope:** `pydmvl` public client

## Summary

Expose the account-screen metadata returned by the authentication action as an
`AccountInfo` object on the session: organization, address, contacts, settings
flags, and counts, plus the raw response for callers that need a field not yet
modelled.

## Motivation

Consumers (the Home Assistant integration) need account metadata that the
curated `Session` does not model: the organization name, the address, contact
e-mails/phone, the service settings, and the number of counters/charges/
receipts. The data is already in the authentication response; this spec
surfaces it without making the consumer parse raw JSON.

## Requirements

- R1 (MUST) `Session.account: AccountInfo` carries the account metadata.
- R2 (MUST) `AccountInfo` fields (all optional, parsed defensively):
  - `organization` (`name`), `database` (`db`), `developer_email`
    (`dev_email`), `contact_email` (`memail`), `address` (`maddr`),
    `flat` (`mflat`, stripped), `management_key` (`mgfkey`), `full_name`
    (`fls_fio`);
  - `phone` (`usersInfo.phone`), `contact` (`contact`);
  - `settings`: `Mapping[str, Any]` from the `settings` object;
  - counts: `charges`, `receipts`, `counters`, `payments`, `news` (lengths of
    the corresponding arrays).
- R3 (MUST) `AccountInfo.raw: Mapping[str, Any]` is the parsed authentication
  response body, so any field not yet modelled is reachable. `raw` is the
  existing `Session` payload; no extra request is made.
- R4 (MUST) No credential is exposed by default: `AccountInfo` never contains
  the submitted password and does not single out the `hash` field into a named
  attribute below `raw`. The `hash` remains present in `raw` only because it is
  part of the server response; `raw` is excluded from `repr` so a logged or
  formatted session never prints it, and callers must not log or publish
  `raw`.
- R5 (MUST) `Session` keeps every existing field and property; the change is
  additive and backward compatible.
- R6 (MUST) Parsing is defensive: missing/None fields become `None`/empty and
  never raise; a malformed `settings` object yields an empty mapping.

## Design

- New frozen dataclass `AccountInfo` in `models.py`, built by a
  `parse_account_info(payload, *, charges, receipts)` helper during
  `parse_session`.
- `Session` gains `account: AccountInfo`; `database`/`name` remain on
  `Session` for compatibility (and are also reachable via `account`).
- `AccountInfo.raw` (and `Session.account`) are excluded from `repr` so a
  logged session never prints the server `hash` or account data.
- Counts: `charges`/`receipts` come from the already-parsed tuples; `counters`,
  `payments`, `news` are the corresponding array lengths.

## API

- New export: `AccountInfo`.
- `Session.account: AccountInfo`; `Session` otherwise unchanged.

## Test plan

- Parse a synthetic authentication fixture: organization/address/contacts/
  settings/counts and `raw` are populated; missing fields are `None`.
- A partial payload (no settings/usersInfo) parses without raising.
- `raw` contains the response keys; no named field equals the password hash
  value.
- Existing `Session`/`AccountSummary` tests stay green (backward compatible).

## Acceptance criteria

- Gate green (`ruff check`, `ruff format --check`, `mypy`, `pytest -m "not
  live"`); new code covered; skeptic without `BLOCKING`.

## Out of scope

- Typed models for every nested array (counters, charges details); `raw`
  covers them until a dedicated spec.
- Any account-changing call.

## Status

`implemented` (2026-10-02) — `Session.account: AccountInfo` with metadata,
settings, counts and `raw`; exported as `AccountInfo`; version 0.2.0.
