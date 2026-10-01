"""Credential redaction for the httpx request logger.

The service authenticates through query parameters (spec 0001), so request
URLs contain the account login and the password hash. Some httpx versions log
the full URL at INFO level; this filter rewrites those URLs before they reach
any handler so credentials are never emitted, on any supported httpx version.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

REDACTED = "***"
SENSITIVE_QUERY_KEYS = frozenset({"login", "hash"})


QueryValue = str | int | float | bool | None


def redact_url(url: httpx.URL) -> httpx.URL:
    """Return a copy of ``url`` with sensitive query values replaced."""
    items: list[tuple[str, QueryValue]] = [
        (key, REDACTED if key in SENSITIVE_QUERY_KEYS else value)
        for key, value in url.params.multi_items()
    ]
    if not items:
        return url
    query = str(httpx.QueryParams(items)).encode("ascii")
    return url.copy_with(query=query)


def _redact_arg(value: Any) -> Any:
    return redact_url(value) if isinstance(value, httpx.URL) else value


class RedactCredentialsFilter(logging.Filter):
    """Rewrite httpx log records so credentials never leave the process."""

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple):
            record.args = tuple(_redact_arg(arg) for arg in args)
        elif isinstance(args, dict):
            record.args = {key: _redact_arg(value) for key, value in args.items()}
        return True


def install_httpx_redaction() -> None:
    """Attach the redaction filter to the httpx logger once (idempotent)."""
    logger = logging.getLogger("httpx")
    if not any(isinstance(flt, RedactCredentialsFilter) for flt in logger.filters):
        logger.addFilter(RedactCredentialsFilter())
