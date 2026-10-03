# 0005 — Known API surface

- **Status:** implemented
- **Scope:** catalogue of known actions of the account API and their coverage
  in this library

## Summary

The service exposes a single PHP router at `api.php` with an `action` query
parameter. This spec is the catalogue of actions known to this project and the
source of truth for coverage. Only the read-only subset needed for the account
snapshot is implemented.

## Motivation

The API is larger than what this library implements. Keeping an explicit
catalogue prevents silent scope creep and documents what is intentionally out
of scope.

## Requirements

- R1 (MUST) The catalogue lists every known action with a short, behavior-only
  description and an implementation status.
- R2 (MUST) Adding an action section is a reviewable change alongside its spec
  and implementation.

## Coverage

Legend: **implemented** — exercised by `pydmvl`; **out of scope** — known but
not implemented, usually a writing action.

| Action | Purpose | Status |
|---|---|---|
| `authentication` | Authenticate and return the account snapshot (aggregates, charges, receipts, payments, counters) | implemented |
| `forgotpassword` | Password recovery and change | out of scope |
| `savetoken` | Save the device push token | out of scope |
| `deletetoken` | Clear the device push token | out of scope |
| `generatecode` | Set a quick access code | out of scope |
| `deleteaccount` | Delete the account record | out of scope |
| `getversion` | Application update gate | out of scope |
| `getpayments` | Amount due by payment channel (segments: provider, button, amount, tax) | implemented |
| `addpayment` | Create a payment link or QR code | out of scope |
| `addcounter` | Submit a meter reading | out of scope |
| `delcounter` | Delete a meter reading | out of scope |
| `addguard` | Request a security pass | out of scope |
| `getguards` | List permanent passes | out of scope |
| `revokeguard` | Revoke a permanent pass | out of scope |
| `addguard2` | Create a pass | out of scope |
| `delguard` | Delete a pass | out of scope |
| `opendoor` | Open a door or camera | out of scope |
| `favouritedoorcam` | Add/remove a camera or door from favourites | out of scope |
| `addmessage` | Send a message | out of scope |
| `addrequest` | Create a dispatcher request | out of scope |
| `addfeedback` | Email a dispatcher request | out of scope |
| `addpoll` | Answer a poll | out of scope |
| `closepoll` | Decline a poll | out of scope |
| `addvoting` | Submit a vote | out of scope |
| `votinglogin` | Log in to a vote | out of scope |
| `deletenotification` | Delete a notification | out of scope |
| `makenotificationread` | Mark a notification read | out of scope |
| `readallpush` | Mark all notifications read | out of scope |
| `addpushtable` | Register a device for push | out of scope |
| `agetuserinfo` | Update user information | out of scope |

## Design

- The implemented scope is the `authentication` action, parsed by specs 0002
  (documents), 0003 (payment history), 0006 (counters, read-only), and 0007
  (account info), plus the read-only `getpayments` action (amount-due segments,
  spec 0008). `getpayments` is read-only and does not create a payment.
- All other actions are intentionally unimplemented; most write state and are
  out of scope for a read-only client.

## API

Not applicable: this spec defines no public API of its own.

## Test plan

- The catalogue is documentation; coverage changes are reviewed with the
  accompanying spec and the implementation that supports them.
- New actions are added together with their spec, tests, and implementation,
  or explicitly marked out of scope here.

## Acceptance criteria

- The catalogue matches the library's implemented behavior.

## Out of scope

- The chat/WebSocket host and other non-`action` endpoints.
- Writing actions of any kind.

## Status

`implemented` (2026-10-01: catalogue for the 0.1.0 scope; 2026-10-03:
`getpayments` amount-due segments implemented in 0.4.0, spec 0008).
