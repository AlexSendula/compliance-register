from pathlib import Path
import pytest


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A throwaway project with an empty knowledge-base/."""
    (tmp_path / "knowledge-base").mkdir()
    return tmp_path
