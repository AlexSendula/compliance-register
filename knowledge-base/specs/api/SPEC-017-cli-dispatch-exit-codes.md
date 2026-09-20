---
id: SPEC-017
title: 'CLI dispatch, exit-code contract and refusal boundary (main)'
category: api
tags: [api, cli, exit-codes, D29, principle-9, principle-10]
status: implemented
certainty: 92
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/cli.py
  - compliance_register/paths.py
  - compliance_register/frontmatter.py
  - compliance_register/sources.py
  - tests/test_cli.py
intentional_decisions:
  - "argparse usage errors are remapped from exit 2 to exit 1"
  - "Only four exception types are caught; anything else propagates with a traceback"
  - "No --project flag; the root is discovered from the working directory"
behaviors:
  - behavior_id: BEH-169
    title: 'Running any command outside a directory tree that contains knowledge-base/ exits 2 with a message naming knowledge-base'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_outside_project_exits_2
  - behavior_id: BEH-170
    title: 'A malformed argument (e.g. --today tomorrow) exits 1, not argparse''s 2, and the argparse message reaches stderr'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_today_must_be_an_iso_date
  - behavior_id: BEH-171
    title: '--version prints ''compliance-register <version>'' to stdout and exits 0'
    state: deprecated
    level: component
    adapter: pytest
    locator: tests/test_launcher.py::test_launcher_prints_version
  - behavior_id: BEH-172
    title: 'Invoking the CLI with no subcommand prints help to stderr and exits 1'
    state: confirmed
    level: component
    adapter: pytest
  - behavior_id: BEH-173
    title: 'A corrupt sources.json surfaces as ''error: sources.json: ...'' on stderr with exit 1 from check'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_corrupt_sources_json_is_a_typed_error_and_exit_1
  - behavior_id: BEH-174
    title: 'A profile diff whose git ref cannot be read exits 1 and relays git''s stderr'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_profile_diff_ref_is_never_a_git_option
---

# CLI dispatch, exit-code contract and refusal boundary (main)

## What

`compliance_register/cli.py` holds terminal I/O and exit codes only; every decision lives in the other modules and `cli.main(argv)` relays their result. The contract is `0` done, `1` failure (bad input, a validator found problems, an unreadable sources.json or frontmatter block), `2` refused (not inside a project with `knowledge-base/`, an unsafe path, or a per-command refusal).

`main` catches argparse's `SystemExit` and returns 1 for any non-zero code (argparse itself exits 2 on a usage error) and 0 for `--version`; no subcommand prints help to stderr and returns 1. `paths.NotAProject` and `paths.UnsafePath` become a `refused: ...` line on stderr and exit 2; `frontmatter.FrontmatterError` and `sources.SourcesError` become `error: ...` and exit 1. Every exception message and every value that came from a file is passed through `render.printable` before it reaches stdout or stderr; `--json` output is emitted raw via `json.dumps`. The project root is found by walking upward from the working directory for a `knowledge-base/` directory (no `--project` flag).

## Why

D29 fixes the three exit codes so an agent driving the CLI can distinguish "done", "something was wrong with the input" and "the tool declined to act" without parsing prose; argparse's own use of 2 for usage errors would collide with "refused", so it is folded into 1. D2 (refined) drops the freya gate dialect: the CLI uses the working directory and `--json`, docs-mirror's convention.

Principle 9 (refuse loudly, never brick) is why every known failure has a clear message and a non-zero exit rather than a traceback, and principle 10 (escape at the sink) is why the exception text itself is escaped: a `FrontmatterError` can quote a line of a regime file, which is untrusted.

Open question: is it intended that an unexpected `OSError` (e.g. a read-only `knowledge-base/`) surfaces as a traceback rather than a `refused:`/`error:` line? Principle 9 is satisfied either way (non-zero exit), but the SKILL.md exit-code table does not say.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-169 Running any command outside a directory tree that contains knowledge-base/ exits 2 with a message naming knowledge-base | accepted | `tests/test_cli.py::test_outside_project_exits_2` |
| BEH-170 A malformed argument (e.g. --today tomorrow) exits 1, not argparse's 2, and the argparse message reaches stderr | accepted | `tests/test_cli.py::test_today_must_be_an_iso_date` |
| BEH-171 --version prints 'compliance-register <version>' to stdout and exits 0 | deprecated | `tests/test_launcher.py::test_launcher_prints_version` |
| BEH-172 Invoking the CLI with no subcommand prints help to stderr and exits 1 | confirmed | — (test owed) |
| BEH-173 A corrupt sources.json surfaces as 'error: sources.json: ...' on stderr with exit 1 from check | accepted | `tests/test_poisoned_files_do_not_brick.py::test_corrupt_sources_json_is_a_typed_error_and_exit_1` |
| BEH-174 A profile diff whose git ref cannot be read exits 1 and relays git's stderr | accepted | `tests/test_cli.py::test_profile_diff_ref_is_never_a_git_option` |

## Intentional Design Decisions

### argparse usage errors are remapped from exit 2 to exit 1

**Decision**: `main` catches `SystemExit` from `parse_args` and returns 1 for any non-zero code, so a bad flag, an unknown subcommand or a malformed `--today` exits 1, never 2.

**Rationale**: D29 reserves 2 for "refused" (not in a project, missing dependency, nothing to check, validation failed before a request). A usage error is bad input, which is 1. An agent reading the code must not mistake a typo for a refusal.

**Security Scan Note**: Swallowing `SystemExit` is deliberate and narrow: only the code is inspected and the original stderr message from argparse has already been printed. Not an error-hiding defect.

### Only four exception types are caught; anything else propagates with a traceback

**Decision**: `main` handles `NotAProject` and `UnsafePath` (exit 2) and `FrontmatterError` and `SourcesError` (exit 1). `OSError`, `KeyError` and other unexpected exceptions are not caught.

**Rationale**: Known, expected failures get a one-line message and a documented code. An unexpected exception is a bug, and a traceback is more useful to the person reporting it than a generic "error" line. Principle 9 wants loud refusal, not blanket suppression.

**Security Scan Note**: A catch-all `except Exception` in `main` would hide bugs; its absence is intentional. Inside the loop over sources (check.py/fetch.py) exceptions ARE caught per source, which is the boundary principle 9 actually names.

### No --project flag; the root is discovered from the working directory

**Decision**: `paths.find_root()` walks upward from cwd looking for `knowledge-base/`; there is no argument to point the CLI at another directory.

**Rationale**: D2 refined: the freya gate dialect (`--project .`, `--format json`) was dropped for docs-mirror's convention. Running outside a project is a refusal (exit 2) with a message naming `knowledge-base/`.

**Security Scan Note**: Every write is then confined under `<root>/knowledge-base/compliance/` via `paths.contained`; a `--project` flag would have been one more user-controlled path to contain.

## Related Specs

- [SPEC-018: init: idempotent scaffold of knowledge-base/compliance/](./SPEC-018-init-scaffold.md)
- [SPEC-019: status, pending, search: read-only reports](./SPEC-019-status-pending-search.md)
- [SPEC-020: resolve: record a named human's decision on a pending entry](./SPEC-020-resolve.md)
- [SPEC-021: Validators: profile validate, regimes validate, sources validate](./SPEC-021-validators.md)
- [SPEC-022: profile diff --against with --end-of-options](./SPEC-022-profile-diff.md)
- [SPEC-023: Watch commands at the CLI: fetch, check, rescan](./SPEC-023-watch-commands-cli.md)
- [SPEC-024: render.printable: escape at the terminal sink](./SPEC-024-render-printable.md)
- [SPEC-027: Launcher and preflight](./SPEC-027-launcher-preflight.md)
- [SPEC-001: Profile: 15 dimensions, propose/confirm lifecycle, null blocks](../features/SPEC-001-profile-dimensions-propose-confirm.md)
- [SPEC-002: Regimes: one file per regime, frontmatter validation, obligation parsing and counts](../features/SPEC-002-regimes-one-file-per-regime.md)
- [SPEC-003: Pending: append-only pending.jsonl and resolutions.jsonl with replay-derived state](../features/SPEC-003-pending-append-only-logs.md)
- [SPEC-015: fetch command: acquire confirmed sources into the mirror](../integration/SPEC-015-fetch-command.md)
- [SPEC-016: check command: three-valued freshness, pending entries, date-passed and profile-stale](../integration/SPEC-016-check-command.md)
- [SPEC-028: Paths: project root discovery and write containment](../infra/SPEC-028-paths-root-discovery-and-write-containment.md)
- [SPEC-029: Frontmatter: YAML block read/write, atomic save, ISO date normalisation](../infra/SPEC-029-frontmatter-yaml-atomic-save-date-normalisation.md)
- [SPEC-030: Packaging: SKILL.md contract, plugin manifests, path launcher and version](../infra/SPEC-030-packaging-skill-md-plugin-launcher-version.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan by freya-spec-manager |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed); --version duplicate deprecated in favour of BEH-229 | First behaviour review after the freya wrap-up |
