from pathlib import Path
import pytest

from compliance_register import paths


def test_find_root_walks_up(project: Path):
    deep = project / "src" / "app"
    deep.mkdir(parents=True)
    assert paths.find_root(deep) == project


def test_find_root_refuses_outside_project(tmp_path: Path):
    with pytest.raises(paths.NotAProject):
        paths.find_root(tmp_path)


def test_compliance_dir(project: Path):
    assert paths.compliance_dir(project) == project / "knowledge-base" / "compliance"


def test_contained_accepts_child(project: Path):
    base = paths.compliance_dir(project)
    base.mkdir()
    assert paths.contained(base, Path("regimes/GDPR.md")) == base / "regimes" / "GDPR.md"


def test_contained_refuses_escape(project: Path):
    base = paths.compliance_dir(project)
    base.mkdir()
    with pytest.raises(paths.UnsafePath):
        paths.contained(base, Path("../secrets.md"))


@pytest.mark.parametrize("bad", ["../x", "a/b", "GDPR ", "", ".hidden", "x y"])
def test_safe_component_rejects(bad):
    with pytest.raises(paths.UnsafePath):
        paths.safe_component(bad)


def test_safe_component_accepts():
    assert paths.safe_component("GDPR") == "GDPR"
    assert paths.safe_component("eurlex-32016R0679") == "eurlex-32016R0679"
