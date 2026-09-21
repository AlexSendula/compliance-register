from pathlib import Path
import pytest

from compliance_register import frontmatter as fm, paths, sources
from compliance_register.mirror import store
from tests.test_sources import EURLEX


def src(**over):
    return sources.Source.from_dict(dict(EURLEX, **over))


def test_source_dir_public_and_private(project: Path):
    cdir = paths.compliance_dir(project)
    assert store.source_dir(cdir, src()) == cdir / "mirror" / "eu" / "eu-eurlex-32016R0679"
    priv = src(licence={"redistribute": False, "attribution": None})
    assert store.source_dir(cdir, priv) == cdir / "mirror" / ".private" / "eu" / "eu-eurlex-32016R0679"


def test_write_page_adds_provenance(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    p = store.write_page(cdir, src(), "02016R0679-20160504/art_32.md", {"article": 32, "version": "02016R0679-20160504"}, "## Article 32\ntext\n", retrieved_at="2026-09-20T00:00:00Z")
    meta, body = fm.load(p)
    assert meta["source"] == "eu-eurlex-32016R0679" and meta["article"] == 32
    assert meta["content_hash"] == store.content_hash("## Article 32\ntext\n")
    assert meta["licence"]["redistribute"] is True and body.startswith("## Article 32")
    assert meta["licence"]["name"] == "CC-BY-4.0" and meta["licence_name"] == "CC-BY-4.0"


def test_write_page_licence_name_is_optional(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    p = store.write_page(cdir, src(licence={"redistribute": True, "attribution": "x"}), "a.md", {}, "t\n", retrieved_at="2026-09-20")
    assert fm.load(p)[0]["licence_name"] is None


def test_write_page_refuses_escape(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    with pytest.raises(paths.UnsafePath):
        store.write_page(cdir, src(), "../../evil.md", {}, "x", retrieved_at="t")


def test_manifest_roundtrip(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    assert store.load_manifest(cdir, src()) == {}
    store.save_manifest(cdir, src(), {"https://x/1": {"fetched": "2026-09-20", "lastmod": "2026-09-01", "hash": "h", "path": "1.md", "version": None}})
    assert store.load_manifest(cdir, src())["https://x/1"]["hash"] == "h"


def test_needs_refresh_rules():
    assert store.needs_refresh(None, "2026-01-01", None)
    assert store.needs_refresh({"lastmod": None}, "2026-01-01", None)
    assert store.needs_refresh({"lastmod": "2026-01-01"}, None, None)
    assert not store.needs_refresh({"lastmod": "2026-01-01"}, "2026-01-01", None)
    assert store.needs_refresh({"lastmod": "2026-01-01"}, "2026-02-01", None)
    assert not store.needs_refresh({"hash": "a"}, None, "a")
    assert store.needs_refresh({"hash": "a"}, None, "b")


def test_content_hash_ignores_whitespace():
    assert store.content_hash("a  b\n\nc") == store.content_hash("a b c")


def test_private_page_ensures_mirror_gitignore(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    priv = src(licence={"redistribute": False, "attribution": None})
    gi = cdir / "mirror" / ".gitignore"
    store.write_page(cdir, priv, "a.md", {}, "t\n", retrieved_at="2026-09-20")
    assert gi.read_text().splitlines() == [".private/"]
    gi.write_text("# mine\n")
    store.write_page(cdir, priv, "b.md", {}, "t\n", retrieved_at="2026-09-20")
    assert gi.read_text().splitlines() == ["# mine", ".private/"]
    store.write_page(cdir, priv, "c.md", {}, "t\n", retrieved_at="2026-09-20")
    assert gi.read_text().count(".private/") == 1
    store.write_page(cdir, src(), "d.md", {}, "t\n", retrieved_at="2026-09-20")  # a public page does not touch it


@pytest.mark.parametrize("over", [{"id": "../evil"}, {"id": ".hidden"}, {"jurisdiction": "EU/.."}, {"jurisdiction": "e u"}])
def test_a_jurisdiction_or_source_id_that_is_not_a_safe_path_component_raises_unsafe_path(project: Path, over):
    with pytest.raises(paths.UnsafePath):
        store.source_dir(paths.compliance_dir(project), src(**over))
