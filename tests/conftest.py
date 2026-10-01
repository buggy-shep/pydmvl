"""Shared test helpers: fixture loading and mock transport wiring.

All fixtures under tests/fixtures/ are synthetic; no real account data may
ever be committed here.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from pydmvl import AsyncDmvlClient, DmvlClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"

LOGIN = "user@example.com"
PASSWORD = "correct-horse-battery-staple"


def load_fixture(name: str) -> Any:
    """Load a synthetic API fixture by file name."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def synthetic_session_payload() -> dict[str, Any]:
    """A copy of the synthetic authentication fixture (safe to mutate)."""
    return copy.deepcopy(load_fixture("authentication.json"))


def json_response(payload: Any, status: int = 200) -> httpx.Response:
    """Build a JSON httpx.Response for a mock handler."""
    return httpx.Response(status_code=status, json=payload)


def make_client(handler: Callable[[httpx.Request], httpx.Response], **kwargs: Any) -> DmvlClient:
    """Build a DmvlClient wired to an httpx.MockTransport handler."""
    return DmvlClient(transport=httpx.MockTransport(handler), **kwargs)


def make_async_client(
    handler: Callable[[httpx.Request], httpx.Response], **kwargs: Any
) -> AsyncDmvlClient:
    """Build an AsyncDmvlClient wired to an httpx.MockTransport handler."""
    return AsyncDmvlClient(transport=httpx.MockTransport(handler), **kwargs)
