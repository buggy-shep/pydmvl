"""Import smoke tests and packaging guards (spec 0004 R5/R6)."""

import re
import tomllib
from pathlib import Path

import pydmvl

PUBLIC_API = {
    "AccountSummary",
    "ApiError",
    "AsyncDmvlClient",
    "AuthError",
    "Charge",
    "Credentials",
    "DmvlClient",
    "DmvlError",
    "OutstandingPayment",
    "Payment",
    "Receipt",
    "Session",
    "password_hash",
}


def test_package_imports() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", pydmvl.__version__)


def test_public_api_surface() -> None:
    """The package root exports the complete public API (spec 0004 R5)."""
    assert set(pydmvl.__all__) == PUBLIC_API | {"__version__"}
    for name in PUBLIC_API:
        assert getattr(pydmvl, name) is not None


def test_version_matches_pyproject() -> None:
    """Distribution and package versions stay in sync (spec 0004 R5)."""
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with pyproject.open("rb") as handle:
        version = tomllib.load(handle)["project"]["version"]
    assert version == pydmvl.__version__


def test_httpx_dependency_floor() -> None:
    """The httpx floor stays Home Assistant compatible (spec 0004 R6)."""
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with pyproject.open("rb") as handle:
        dependencies = tomllib.load(handle)["project"]["dependencies"]
    assert "httpx>=0.27" in dependencies
