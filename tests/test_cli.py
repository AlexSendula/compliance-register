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


def test_profile_validate_fails_while_any_answer_is_still_proposed(project: Path):
    """The seam that made exit 0 read as "stage 1 done": a profile of agent
    proposals nobody has confirmed must not pass."""
    run(["init"], project)
    cdir = paths.compliance_dir(project)
    meta, body = fm.load(cdir / "profile.md")
    for slug in profile.DIMENSIONS:
        meta["answers"][slug] = {"value": "x", "status": "confirmed", "evidence": []}
    meta["answers"]["size"] = {"value": "guess", "status": "proposed", "evidence": ["pyproject.toml"]}
    meta["confirmed_by"], meta["confirmed_at"] = "Alex", "2026-09-22"
    fm.save(cdir / "profile.md", meta, body)
    code, out, err = run(["profile", "validate"], project)
    assert code == 1
    assert "size: proposed, not confirmed" in out
    assert "confirmed_by and confirmed_at set while 1 answer(s) are not confirmed" in out
    # and rescan still runs: the snapshot never took the proposed value anyway
    assert run(["rescan"], project)[0] == 0


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
        raise subprocess.CalledProcessError(128, cmd, stderr="fatal: bad revision \x1b[31mred\x1b[0m")
    monkeypatch.setattr(subprocess, "run", fake_run)
    code, _, err = run(["profile", "diff", "--against=--output=/tmp/x"], project)
    assert code == 1 and "bad revision" in err and "\x1b" not in err  # git's stderr is a sink too (P10)
    assert seen["cmd"][:3] == ["git", "show", "--end-of-options"] and seen["cmd"][3].startswith("--output=/tmp/x:")


def test_today_must_be_an_iso_date(project: Path):
    run(["init"], project)
    for cmd in (["check"], ["fetch"], ["rescan"]):
        code, _, err = run([*cmd, "--today", "tomorrow"], project)
        assert code == 1 and "YYYY-MM-DD" in err, cmd
    assert run(["rescan", "--today", "2026-13-40"], project)[0] == 1


def test_invoking_the_cli_with_no_subcommand_prints_help_to_stderr_and_exits_1(tmp_path: Path):
    code, out, err = run([], tmp_path)
    assert code == 1 and out == "" and err.startswith("usage: compliance-register")


def test_init_does_not_append_a_duplicate_search_index_json_line_to_an_existing_gitignore(project: Path):
    cdir = paths.compliance_dir(project); cdir.mkdir(parents=True)
    (cdir / ".gitignore").write_text("scratch/\n.search-index.json\n")
    code, _, err = run(["init"], project)
    assert code == 0, err
    assert (cdir / ".gitignore").read_text().splitlines() == ["scratch/", ".search-index.json"]


def test_pending_prints_no_pending_changes_and_search_prints_the_no_hits_hint_on_empty_results_both_exit_0(project: Path):
    run(["init"], project)
    assert run(["pending"], project)[:2] == (0, "no pending changes\n")
    assert run(["search", "nothing matches this"], project)[:2] == (0, "no hits — try the source's own vocabulary\n")


def test_resolve_with_an_id_that_is_not_open_prints_unknown_pending_id_to_stderr_and_exits_1(project: Path):
    run(["init"], project)
    code, out, err = run(["resolve", "chg-9999", "--action", "applied", "--by", "Alex"], project)
    assert code == 1 and out == "" and "unknown pending id: chg-9999" in err


def test_resolve_without_by_or_with_an_action_outside_applied_dismissed_deferred_is_an_argparse_error_and_exits_1(project: Path):
    run(["init"], project)
    code, _, err = run(["resolve", "chg-0001", "--action", "applied"], project)
    assert code == 1 and "--by" in err
    code, _, err = run(["resolve", "chg-0001", "--action", "ignored", "--by", "Alex"], project)
    assert code == 1 and "invalid choice" in err


def test_the_success_line_prints_the_id_and_the_by_name_through_printable(project: Path):
    """pending.jsonl is hand-editable, --by is operator text: both are sinks (P10)."""
    run(["init"], project)
    row = {"id": "chg-\x1b[2J", "kind": "date-passed", "severity": "major", "summary": "x"}
    (paths.compliance_dir(project) / "pending.jsonl").write_text(json.dumps(row) + "\n")
    code, out, err = run(["resolve", "chg-\x1b[2J", "--action", "applied", "--by", "Al\x1b[2Jex"], project)
    assert code == 0, err
    assert out == "chg-\\x1b[2J applied by Al\\x1b[2Jex\n" and "\x1b" not in out


def test_profile_validate_without_a_profile_md_prints_no_profile_md_run_init_to_stderr_and_exits_1(project: Path):
    code, out, err = run(["profile", "validate"], project)
    assert code == 1 and out == "" and "no profile.md — run init" in err


def test_diff_without_a_current_profile_md_prints_no_profile_md_to_stderr_and_exits_1(project: Path):
    code, out, err = run(["profile", "diff", "--against", "HEAD"], project)
    assert code == 1 and out == "" and "no profile.md" in err


def test_regimes_validate_prints_id_problem_lines_and_exits_1_when_any_regime_has_problems(project: Path):
    run(["init"], project)
    from tests.test_regimes import META, write
    cdir = paths.compliance_dir(project)
    write(cdir, META)
    assert run(["regimes", "validate"], project)[:2] == (0, "")
    write(cdir, dict(META, id="DSA", applies={"quote": None, "cite": None}))
    code, out, _ = run(["regimes", "validate"], project)
    assert code == 1 and out.splitlines() == ["DSA: applies: quote and cite are required when status is binds"]


def test_regimes_validate_exits_1_and_prints_id_problem_for_a_regime_whose_frontmatter_does_not_parse_while_still_loading_the_others(project: Path):
    run(["init"], project)
    from tests.test_regimes import META, write
    cdir = paths.compliance_dir(project)
    (cdir / "regimes" / "BAD.md").write_text("---\nid: [unterminated\n---\n\nbody\n")
    write(cdir, dict(META, id="DSA", applies={"quote": None, "cite": None}))  # sorts after BAD.md
    code, out, _ = run(["regimes", "validate"], project)
    lines = out.splitlines()
    assert code == 1 and len(lines) == 2
    assert lines[0].startswith("BAD: unreadable: ") and lines[1].startswith("DSA: applies:")


def _fake_network(monkeypatch, project: Path):
    """Route the CLI's default Http client through test_check's scripted routes."""
    from tests.test_check import setup
    from compliance_register.mirror import http
    cdir, factory = setup(project)
    monkeypatch.setattr(http, "_default_opener", factory(None).opener)
    return cdir


def test_check_json_prints_the_report_as_json_with_the_three_counts_and_details(project: Path, monkeypatch):
    _fake_network(monkeypatch, project)
    code, out, err = run(["check", "--json", "--today", "2026-09-20"], project)
    assert code == 0, err
    rep = json.loads(out)
    assert (rep["fresh"], rep["moved"], rep["unreachable"]) == (0, 1, 0)
    assert "newer lastmod" in rep["details"]["nl-reg"]


def test_check_text_output_ends_with_see_compliance_register_pending_only_when_moved_or_unreachable_is_non_zero(project: Path, monkeypatch):
    _fake_network(monkeypatch, project)
    code, out, _ = run(["check", "--today", "2026-09-20"], project)
    assert code == 0 and out.startswith("fresh 0 · moved 1 · unreachable 0\n") and out.endswith("\nsee: compliance-register pending\n")
    run(["fetch", "--today", "2026-09-20"], project)
    code, out, _ = run(["check", "--today", "2026-09-21"], project)
    assert code == 0 and out.startswith("fresh 1 · moved 0 · unreachable 0\n") and "see:" not in out
