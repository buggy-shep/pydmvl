# pydmvl

[![PyPI version](https://img.shields.io/pypi/v/pydmvl.svg)](https://pypi.org/project/pydmvl/)
[![CI](https://github.com/buggy-shep/pydmvl/actions/workflows/ci.yml/badge.svg)](https://github.com/buggy-shep/pydmvl/actions/workflows/ci.yml)

Unofficial Python client for a homeowner ("Domovladelets") account API. It
authenticates with an account login and password and exposes the account
snapshot the service returns for its home screen: account aggregates,
per-period charges (documents), receipt links, and payment history.

> **Disclaimer.** This project is unofficial and is not affiliated with,
> endorsed by, or sponsored by the "Domovladelets" application or its
> operators. It is built for interoperability with your own account. Use it at
> your own risk; only access accounts you are authorized to access.

## Install

```bash
pip install pydmvl
```

## Status

Authentication, the account snapshot, documents (charges, receipts, unpaid
detection), and payment history are implemented (specs 0001–0004); `0.x` — the
API may still change. See [`specs/`](specs/) for the specifications and their
status.

Capabilities:

- Login with `login` + `hash` (MD5 of the password); stateless session, no
  bearer token — [spec 0001](specs/0001-auth.md)
- Account snapshot with debt/charge/payment aggregates —
  [spec 0002](specs/0002-documents.md)
- Per-period charges and receipt links — [spec 0002](specs/0002-documents.md)
- Payment history and the latest payment — [spec 0003](specs/0003-payments.md)
- Public sync + async client API — [spec 0004](specs/0004-client-api.md)

### Known API surface

The service exposes a single PHP `action` router. The catalogue of known
actions is [spec 0005](specs/0005-api-surface.md); only the read-only subset
needed for the account snapshot is implemented here — writing actions
(submitting meter readings, creating payments, opening doors, sending
messages, and similar) are out of scope.

## Requirements

- Python >= 3.11
- [httpx](https://pypi.org/project/httpx/) >= 0.27

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/pytest -m "not live"
```

Live tests against the real API stay behind the `live` marker and are run
manually only, with credentials from the environment (`DMVL_USERNAME`,
`DMVL_PASSWORD`). Account credentials are sent as request query parameters, so
do not enable request-URL logging while a live client is in use.

## License

[MIT](LICENSE)
