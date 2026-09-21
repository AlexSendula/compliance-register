from pathlib import Path
import pytest


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A throwaway project with an empty knowledge-base/."""
    (tmp_path / "knowledge-base").mkdir()
    return tmp_path


@pytest.fixture(autouse=True)
def _no_dns(monkeypatch):
    """No test resolves a real name: every host is a public address unless a test
    injects its own resolver (SEC-003 tests do)."""
    from compliance_register.mirror import http
    monkeypatch.setattr(http, "resolve", lambda host: ["8.8.8.8"])
