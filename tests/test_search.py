from pathlib import Path

from compliance_register import paths, search
from tests.test_regimes import META, BODY, write


def test_search_finds_the_obligation(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    write(cdir, META)
    write(cdir, dict(META, id="CRD", title="Consumer Rights Directive"), body="## Obligations\n\n### CRD-001 · Withdrawal\n- **You must:** inform about the 14-day withdrawal right\n- **It says:** Art. 9\n")
    hits = search.search(cdir, "record of processing activities", k=2)
    assert hits and hits[0].path.endswith("regimes/GDPR.md") and hits[0].kind == "regime"


def test_index_rebuilds_when_file_changes(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    p = write(cdir, META)
    search.search(cdir, "record")
    sig1 = search.signature(cdir)
    p.write_text(p.read_text() + "\n### GDPR-003 · Encryption\n- **You must:** encrypt at rest\n- **It says:** Art. 32\n")
    assert search.signature(cdir) != sig1
    hits = search.search(cdir, "encrypt at rest")
    assert hits and hits[0].path.endswith("GDPR.md")


def test_stop_words_dropped():
    assert "the" not in search.tokenize("the record of the processing")


def test_private_mirror_pages_are_searchable(project: Path):
    """mirror/.private/ is gitignored for committing, not hidden from local use —
    the non-redistributable sources are the ones most worth quoting."""
    cdir = paths.compliance_dir(project); cdir.mkdir()
    page = cdir / "mirror" / ".private" / "x" / "y.md"
    page.parent.mkdir(parents=True)
    page.write_text("## Terms\nchargeback liability rests with the merchant\n")
    (cdir / "mirror" / ".hidden.md").write_text("chargeback liability dotfile\n")
    hits = search.search(cdir, "chargeback liability")
    assert [h.kind for h in hits] == ["mirror"] and hits[0].path.endswith(".private/x/y.md")


def test_tokenize_keeps_accented_words():
    assert search.tokenize("bescherming persoonsgegevens ćirilica") == ["bescherming", "persoonsgegevens", "ćirilica"]


def test_poisoned_index_path_outside_cdir_is_skipped(project: Path):
    import json
    cdir = paths.compliance_dir(project); cdir.mkdir()
    write(cdir, META)
    secret = project / "secret.txt"; secret.write_text("record of processing SECRET\n")
    search.search(cdir, "record")  # builds the index
    table = json.loads((cdir / search.INDEX_FILE).read_text())
    table["docs"][0]["path"] = str(secret)
    (cdir / search.INDEX_FILE).write_text(json.dumps(table))
    hits = search.search(cdir, "record of processing")
    assert hits == [] or all("SECRET" not in h.snippet and str(secret) != h.path for h in hits)
