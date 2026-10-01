"""Live tests against the real API (manual only, `live` marker).

Run with credentials in the environment:

    DMVL_USERNAME=... DMVL_PASSWORD=... .venv/bin/pytest -m live
"""

from __future__ import annotations

import os

import pytest

from pydmvl import DmvlClient

pytestmark = pytest.mark.live


def test_live_login_returns_session() -> None:
    login = os.environ.get("DMVL_USERNAME")
    password = os.environ.get("DMVL_PASSWORD")
    if not login or not password:
        pytest.skip("DMVL_USERNAME/DMVL_PASSWORD are not set")

    with DmvlClient() as client:
        session = client.login(login, password)

    assert session.login == login
    assert session.personal_account is not None
