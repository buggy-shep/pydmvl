# pydmvl

[![PyPI version](https://img.shields.io/pypi/v/pydmvl.svg)](https://pypi.org/project/pydmvl/)
[![CI](https://github.com/buggy-shep/pydmvl/actions/workflows/ci.yml/badge.svg)](https://github.com/buggy-shep/pydmvl/actions/workflows/ci.yml)

Unofficial Python client for the **"Domovladelets+"** ("Домовладелец+",
homeowner) account API. It implements the protocol used by the app
([Google Play](https://play.google.com/store/apps/details?id=com.homeowner)):
it authenticates with an account login and password and exposes the account
snapshot the service returns for its home screen: account aggregates,
per-period charges (documents), receipt links, and payment history.

Неофициальный Python-клиент API лицевого счёта приложения **«Домовладелец+»**.
Реализует протокол этого приложения
([Google Play](https://play.google.com/store/apps/details?id=com.homeowner)):
аутентифицируется по логину и паролю лицевого счёта и предоставляет снимок
счёта, который сервис возвращает для главного экрана: агрегаты по счёту,
начисления за период (документы), ссылки на квитанции и историю платежей.

> **Disclaimer.** This project is unofficial and is not affiliated with,
> endorsed by, or sponsored by the "Domovladelets+" application or its
> operators. It is built for interoperability with your own account. Use it at
> your own risk; only access accounts you are authorized to access.

> **Отказ от ответственности.** Проект неофициальный и не связан с
> приложением «Домовладелец+» или его операторами, не одобрен и не
> спонсируется ими. Он создан для взаимодействия с вашим собственным лицевым
> счётом. Используйте его на свой риск; получайте доступ только к тем счетам,
> на которые у вас есть разрешение.

## Install

```bash
pip install pydmvl
```

## Usage

```python
from pydmvl import DmvlClient

with DmvlClient() as client:
    session = client.login("user", "secret")
    print(session.personal_account.amount_due)
```

## TLS verification (disabled by default)

The service presents an **incomplete certificate chain** (it does not serve the
intermediate CA), so standard verification fails against the real endpoint with
`certificate verify failed: unable to get local issuer certificate`. The
official client disables verification for this reason, and `pydmvl` matches
that observed behavior: `verify` defaults to `False`.

This is a deliberate, documented default, not a silent downgrade. Whenever you
can, turn verification back on — pass a CA bundle that includes the missing
intermediate, or `verify=True` if your trust store already chains the
certificate:

```python
DmvlClient(verify="/path/to/ca-bundle.pem")
```

Consumers that expose TLS settings to end users should present this as an
explicit opt-in control. See [spec 0004](specs/0004-client-api.md) R8.

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
- Configurable TLS verification (default off; see below) — [spec 0004](specs/0004-client-api.md) R8

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
