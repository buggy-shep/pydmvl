"""Unofficial Python client for the homeowner account API.

Disclaimer: this project is unofficial and is not affiliated with the
"Domovladelets" application or its operators. It is intended for use with your
own account.
"""

from .aclient import AsyncDmvlClient
from .auth import Credentials, password_hash
from .client import DmvlClient
from .errors import ApiError, AuthError, DmvlError
from .models import (
    AccountInfo,
    AccountSummary,
    Charge,
    Counter,
    CounterReading,
    OutstandingPayment,
    Payment,
    PaymentOptions,
    PaymentSegment,
    Receipt,
    Session,
)

__version__ = "0.5.0"

__all__ = [
    "AccountInfo",
    "AccountSummary",
    "ApiError",
    "AsyncDmvlClient",
    "AuthError",
    "Charge",
    "Counter",
    "CounterReading",
    "Credentials",
    "DmvlClient",
    "DmvlError",
    "OutstandingPayment",
    "Payment",
    "PaymentOptions",
    "PaymentSegment",
    "Receipt",
    "Session",
    "__version__",
    "password_hash",
]
