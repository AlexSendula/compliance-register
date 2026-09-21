from pathlib import Path

from compliance_register import frontmatter as fm, paths, regimes

META = {
    "id": "GDPR",
    "title": "General Data Protection Regulation",
    "status": "binds",
    "jurisdiction": "EU",
    "sources": [{"id": "eu-eurlex-32016R0679", "version": "02016R0679-20160504", "retrieved": "2026-09-20"}],
    "applies": {"quote": "…establishment … in the Union…", "cite": "Art. 3(1)", "triggered_by": [{"establishment": "NL"}]},
    "exempt": {"quote": None, "reason": "no exemption clause applies"},
    "confirmed_by": "Alex",
    "confirmed_at": "2026-09-20",
    "review_by": "2027-09-20",
}

BODY = """## Why this applies to you
Because.

## Obligations

### GDPR-001 · Records of processing
- **When:** you process personal data other than occasionally
- **You must:** keep a record of processing activities
- **How often:** continuously
- **It says:** Art. 30(1) — "Each controller … shall maintain a record"
- **You'd know by:** a record exists
- **Note:** Art. 30(5) does not apply

### GDPR-002 · Unclear one
- **When:** something
- **You must:**
- **It says:**
"""


def write(cdir: Path, meta: dict, body: str = BODY) -> Path:
    d = cdir / "regimes"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{meta['id']}.md"
    fm.save(p, meta, body)
    return p


def test_load_all_parses_obligations(project: Path):
    cdir = paths.compliance_dir(project)
    write(cdir, META)
    rs = regimes.load_all(cdir)
    assert len(rs) == 1
    r = rs[0]
    assert r.id == "GDPR" and r.status == "binds"
    assert [o.id for o in r.obligations] == ["GDPR-001", "GDPR-002"]
    assert r.obligations[0].fields["You must"] == "keep a record of processing activities"
    assert r.obligations[0].title == "Records of processing"


def test_validate_requires_fields():
    bad = dict(META)
    del bad["confirmed_by"]
    bad["status"] = "maybe"
    problems = regimes.validate(bad, BODY)
    assert any("confirmed_by" in p for p in problems)
    assert any("status" in p for p in problems)


def test_validate_ruled_out_needs_reason_and_no_obligations():
    ro = dict(META, status="ruled-out", exempt={"quote": "does not apply to…", "reason": None})
    problems = regimes.validate(ro, BODY)
    assert any("reason" in p for p in problems)
    assert any("obligations" in p for p in problems)


def test_counts(project: Path):
    cdir = paths.compliance_dir(project)
    write(cdir, META)
    write(cdir, dict(META, id="DSA", status="ruled-out", exempt={"quote": "x", "reason": "no hosting"}), body="## Why this does not apply\nNo.\n")
    c = regimes.counts(regimes.load_all(cdir))
    assert c == {
        "binds": 1, "ruled_out": 1, "undetermined": 0, "no_longer_applies": 0,
        "obligations": 2, "obligations_unclear": 1,
    }


def test_filename_must_match_id(project: Path):
    cdir = paths.compliance_dir(project)
    p = write(cdir, META)
    p.rename(p.with_name("WRONG.md"))
    rs = regimes.load_all(cdir)
    assert rs[0].problems and any("filename" in x for x in rs[0].problems)


def test_validate_requires_applies_quote_and_cite_when_status_is_binds():
    for applies in ({"cite": "Art. 3(1)"}, {"quote": "…establishment…"}):
        problems = regimes.validate(dict(META, applies=applies), BODY)
        assert any(p.startswith("applies:") and "quote and cite" in p for p in problems), applies
    assert not any("quote and cite" in p for p in regimes.validate(dict(META, status="undetermined", applies={}), BODY))


def test_validate_reports_duplicate_obligation_ids_and_bullet_keys_outside_the_six_known_ones():
    body = BODY + "\n### GDPR-001 · Again\n- **You must:** x\n- **It says:** y\n- **Bogus:** z\n"
    problems = regimes.validate(META, body)
    assert "obligations: duplicate id GDPR-001" in problems
    assert "GDPR-001: unknown field 'Bogus'" in problems


def test_load_all_returns_an_empty_list_when_regimes_does_not_exist(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir()
    assert regimes.load_all(cdir) == []
