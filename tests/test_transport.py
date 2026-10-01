"""TLS verification configuration tests (spec 0004 R8)."""

from __future__ import annotations

import inspect

import httpx
import pytest

from pydmvl import AsyncDmvlClient, DmvlClient


def test_verify_defaults_to_false() -> None:
    sync_default = inspect.signature(DmvlClient.__init__).parameters["verify"].default
    async_default = inspect.signature(AsyncDmvlClient.__init__).parameters["verify"].default
    assert sync_default is False
    assert async_default is False


class _StubClient:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs

    def close(self) -> None:
        return None

    async def aclose(self) -> None:
        return None


def test_verify_is_forwarded_to_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _capture(**kwargs: object) -> _StubClient:
        captured.update(kwargs)
        return _StubClient(**kwargs)

    monkeypatch.setattr(httpx, "Client", _capture)

    DmvlClient().close()
    assert captured["verify"] is False

    captured.clear()
    DmvlClient(verify=True).close()
    assert captured["verify"] is True

    captured.clear()
    DmvlClient(verify="/etc/ssl/ca-bundle.pem").close()
    assert captured["verify"] == "/etc/ssl/ca-bundle.pem"


async def test_verify_is_forwarded_to_async_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _capture(**kwargs: object) -> _StubClient:
        captured.update(kwargs)
        return _StubClient(**kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _capture)

    await AsyncDmvlClient().close()
    assert captured["verify"] is False

    captured.clear()
    await AsyncDmvlClient(verify=True).close()
    assert captured["verify"] is True
