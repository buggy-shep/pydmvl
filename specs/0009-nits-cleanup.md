# 0009 — NITS cleanup: flag coercion and spec/README sync

- **Status:** approved
- **Scope:** parser hardening for the `isActual` flag, spec 0004 R1 sync,
  README usage-example sync, and the 0.4.1 patch bump that ships them

## Summary

Follow-up to the NITS recorded after the 0.3.0/0.4.0 work: spec 0004 R1 did not
list `counters` (nor `account`); the README usage example used the sensor name
`amount_due` renamed in 0.3.1; the `isActual` flag (spec 0006 R2) was parsed
with `is True`, so a backend that serializes a boolean as `1` or `"true"` was
silently read as `false`; and edge tests for those representations were
missing. `hideSumWithTax` (spec 0008) keeps its deliberate strict `is True`
parsing and is not part of this change.

## Motivation

The observed responses use real JSON booleans, but the parser should not depend
on that representation: the client is the contract for the Home Assistant
integration, and a non-bool encoding must not silently invert a flag. The
documentation must also match the shipped API.

## Requirements

- R1 (MUST) Spec 0004 R1 lists `counters: tuple[Counter, ...]` and
  `account: AccountInfo` alongside the other `Session` fields.
- R2 (MUST) The README usage example uses only current public API fields (no
  `amount_due`).
- R3 (MUST) The `isActual` flag (spec 0006 R2) is coerced: `bool` as-is; `int`
  where `0` is false and any other integer is true; `str` that, trimmed and
  lower-cased, is `"true"` or `"1"` is true and `"false"`/`"0"`/blank is false;
  any other type or value degrades to `false` (spec 0006 R5). The strict
  `hideSumWithTax` behavior (spec 0008) is unchanged.
- R4 (MUST) Edge tests cover `bool`, `int`, `str` and malformed representations
  for `is_actual`, including `current_reading` selection after coercion.
- R5 (MUST) The change carries the `0.4.1` patch bump in `pyproject.toml` and
  `src/pydmvl/__init__.py` (kept in sync by the existing version test).

## Design

- A pure helper `parse_flag(value) -> bool` in `models.py`; no I/O, no
  exceptions. It is the single place the accepted representations are defined.
- Behavior is intentionally stricter than JavaScript truthiness: the literal
  strings `"false"` and `"0"` are false, so a malformed value never flips a
  flag on.

## API

No public API change: the helper is module-internal; the dataclasses keep their
`bool` fields.

## Test plan

- `isActual` given `true`/`false`, `1`/`0`, `"true"`/`"1"`/`"false"`/`"0"`,
  and a list/`None` (all degrade to false).
- `current_reading` picks the coerced actual reading.

## Acceptance criteria

- Gate green on Python 3.11–3.13; the new edge tests fail before the helper and
  pass after it; the version matches in both files.

## Out of scope

- Coercing unrelated string/date/number fields.
- Changing the observed TLS, auth, or payload semantics.

## Status

`approved` (2026-10-03: NITS follow-up requested in the group conversation).
