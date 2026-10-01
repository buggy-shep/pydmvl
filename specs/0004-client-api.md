# 0004 — Public client API

- **Status:** approved
- **Scope:** `pydmvl` public surface: sync and async clients and the `Session`
  snapshot

## Summary

This spec fixes the public API of the library: the synchronous `DmvlClient`,
the asynchronous `AsyncDmvlClient`, the `Session` snapshot model, and typed
errors. It is the contract consumed by the Home Assistant integration.

## Motivation

Consumers depend on a small, stable surface. The client must be usable both in
synchronous scripts and in the asyncio event loop of Home Assistant, with the
same models and semantics.

## Requirements

- R1 (MUST) `Session` exposes `login`, `name`, `database`,
  `personal_account: AccountSummary`, `charges: tuple[Charge, ...]`,
  `receipts: tuple[Receipt, ...]`, `outstanding: tuple[OutstandingPayment,
  ...]`, plus the derived `has_unpaid_documents` and `last_payment`.
- R2 (MUST) `DmvlClient` and `AsyncDmvlClient` expose the same methods:
  `login(login, password)`, `fetch()`, `logout()`, `close()`. The async client
  additionally supports `async with` (closing on exit); the sync client
  supports `with`.
- R3 (MUST) Both clients accept `base_url`, `version`, `transport`, and
  `timeout` keyword arguments with the same defaults as spec 0001.
- R4 (MUST) Errors: `DmvlError` (base), `AuthError` (authentication), `ApiError`
  (HTTP status or malformed body, carrying `.status`).
- R5 (MUST) The package root exports the full public API and `__version__`; a
  test enforces that the exports and the version stay in sync with
  `pyproject.toml`.
- R6 (MUST) The runtime dependency floor is `httpx>=0.27`, compatible with the
  version pinned by Home Assistant; a test guards the floor.
- R7 (SHOULD) The library logs at debug level only and never logs credentials,
  the password hash, or request URLs.

## Design

- `models.py` holds the parsed dataclasses and pure parsers; `auth.py` holds
  credentials and hashing; `client.py`/`aclient.py` hold the transport and
  mapping to `ApiError`.
- Session state is immutable; each `fetch()` returns a fresh `Session`.

## API

```python
from pydmvl import AsyncDmvlClient, DmvlClient

client = DmvlClient()
session = client.login("user", "secret")
assert session.has_unpaid_documents is not None
latest = session.last_payment
client.close()
```

```python
async with AsyncDmvlClient() as client:
    session = await client.login("user", "secret")
    session = await client.fetch()
```

## Test plan

- Public API surface and version sync tests.
- httpx dependency floor test.
- Sync and async clients driven by the same MockTransport handler.
- Context-manager close behavior for both clients.

## Acceptance criteria

- Gate green on Python 3.11–3.13; sync and async paths covered.

## Out of scope

- Retries, caching, or rate limiting.
- Persistent credential storage (consumers supply credentials at runtime).
- Logging configuration beyond not leaking secrets.

## Status

`approved` (2026-10-01: gate for the 0.1.0 scope).
