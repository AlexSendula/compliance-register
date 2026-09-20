import json
import subprocess
from pathlib import Path

from compliance_register import cli, paths, frontmatter as fm, profile


def run(args, cwd):
    import io, contextlib
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        import os
        old = os.getcwd(); os.chdir(cwd)
        try:
            code = cli.main(args)
        finally:
            os.chdir(old)
    return code, out.getvalue(), err.getvalue()


def test_outside_project_exits_2(tmp_path: Path):
    code, out, err = run(["status"], tmp_path)
    assert code == 2 and "knowledge-base" in err


def test_init_scaffolds(project: Path):
    code, out, err = run(["init"], project)
    assert code == 0, err
    cdir = paths.compliance_dir(project)
    assert (cdir / "profile.md").is_file()
    assert (cdir / "regimes").is_dir() and (cdir / "mirror" / ".gitignore").read_text().strip() == ".private/"
    assert json.loads((cdir / "sources.json").read_text()) == {"schema": 1, "sources": []}
    assert ".search-index.json" in (cdir / ".gitignore").read_text()


def test_init_twice_is_safe(project: Path):
    run(["init"], project)
    code, _, err = run(["init"], project)
    assert code == 0, err


def test_status_json(project: Path):
    run(["init"], project)
    code, out, _ = run(["status", "--json"], project)
    assert code == 0
    rep = json.loads(out)
    assert rep["profile"]["present"] is True and rep["regimes"]["binds"] == 0


def test_profile_validate_fails_on_fresh_profile(project: Path):
    run(["init"], project)
    code, out, err = run(["profile", "validate"], project)
    assert code == 1 and "unanswered" in (out + err)


def test_resolve_and_pending(project: Path):
    run(["init"], project)
    from compliance_register import pending
    e = pending.add(paths.compliance_dir(project), "date-passed", "major", "x", now="2026-10-01")
    code, out, _ = run(["pending", "--json"], project)
    assert json.loads(out)[0]["id"] == e["id"]
    code, _, err = run(["resolve", e["id"], "--action", "applied", "--by", "Alex", "--note", "done"], project)
    assert code == 0, err
    code, out, _ = run(["pending", "--json"], project)
    assert json.loads(out) == []


def test_profile_diff_against_file(project: Path):
    run(["init"], project)
    cdir = paths.compliance_dir(project)
    old = cdir / "old.md"
    old.write_text((cdir / "profile.md").read_text())
    meta, body = fm.load(cdir / "profile.md")
    meta["answers"]["sector"]["value"] = "finance"
    fm.save(cdir / "profile.md", meta, body)
    code, out, _ = run(["profile", "diff", "--against", str(old)], project)
    assert code == 0 and out.strip() == "sector"


def test_search_cli(project: Path):
    run(["init"], project)
    from tests.test_regimes import META, write
    write(paths.compliance_dir(project), META)
    code, out, _ = run(["search", "record of processing", "--json"], project)
    assert code == 0 and json.loads(out)[0]["path"].endswith("GDPR.md")


def test_search_output_escapes_terminal_controls(project: Path):
    """Escape at sink (docs-mirror ADR-008): a mirrored or hand-written body
    can carry ESC (repaints the terminal) or U+202E (reverses what is read)."""
    run(["init"], project)
    from tests.test_regimes import META, write
    write(paths.compliance_dir(project), META, body="## Obligations\n\n### GDPR-001 · Records\n- **You must:** keep a record \x1b[2J of processing ‮activities\n- **It says:** Art. 30\n")
    code, out, _ = run(["search", "record of processing"], project)
    assert code == 0 and "GDPR.md" in out
    assert "\x1b" not in out and "‮" not in out
    assert "\\x1b" in out and "\\u202e" in out


def test_pending_output_escapes_terminal_controls(project: Path):
    run(["init"], project)
    from compliance_register import pending
    pending.add(paths.compliance_dir(project), "source-moved", "major", "moved to \x1b[2Jhttps://evil", now="2026-10-01")
    code, out, _ = run(["pending"], project)
    assert code == 0 and "\x1b" not in out and "\\x1b[2J" in out


def test_sources_validate_cli(project: Path):
    run(["init"], project)
    cdir = paths.compliance_dir(project)
    code, out, _ = run(["sources", "validate"], project)
    assert code == 0
    from compliance_register import sources
    s = sources.Source.from_dict({"id": "x", "jurisdiction": "NL", "kind": "regulator", "url": "http://x.test/", "tier": "api"})
    sources.save(cdir, [s])
    code, out, _ = run(["sources", "validate"], project)
    assert code == 1 and "https" in out and "adapter" in out


def test_rescan_cli_exits_2_on_invalid_profile(project: Path):
    run(["init"], project)
    code, out, err = run(["rescan"], project)
    assert code == 2 and "unanswered" in err


def test_profile_diff_ref_is_never_a_git_option(project: Path, monkeypatch):
    run(["init"], project)
    seen = {}
    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        raise subprocess.CalledProcessError(128, cmd, stderr="fatal: bad revision")
    monkeypatch.setattr(subprocess, "run", fake_run)
    code, _, err = run(["profile", "diff", "--against=--output=/tmp/x"], project)
    assert code == 1 and "bad revision" in err
    assert seen["cmd"][:3] == ["git", "show", "--end-of-options"] and seen["cmd"][3].startswith("--output=/tmp/x:")


def test_today_must_be_an_iso_date(project: Path):
    run(["init"], project)
    for cmd in (["check"], ["fetch"], ["rescan"]):
        code, _, err = run([*cmd, "--today", "tomorrow"], project)
        assert code == 1 and "YYYY-MM-DD" in err, cmd
    assert run(["rescan", "--today", "2026-13-40"], project)[0] == 1
