---
id: SPEC-019
title: 'status, pending, search: read-only reports with --json raw and text escaped'
category: api
tags: [api, cli, status, pending, search, principle-10, principle-9]
status: implemented
certainty: 90
created: 2026-09-20
updated: 2026-09-20
related_code:
  - compliance_register/cli.py
  - compliance_register/status.py
  - compliance_register/pending.py
  - compliance_register/search.py
  - compliance_register/render.py
  - tests/test_cli.py
  - tests/test_poisoned_files_do_not_brick.py
intentional_decisions:
  - "--json output bypasses render.printable"
  - "status, pending and search always exit 0, even when problems are listed"
  - "Fixed-vocabulary fields (kind, action, score) print without escaping"
behaviors:
  - behavior_id: BEH-179
    title: 'status --json returns a report object with profile.present true and regimes.binds 0 on a fresh project'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_status_json
  - behavior_id: BEH-180
    title: 'pending --json lists an added entry and, after resolve, an empty list'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_resolve_and_pending
  - behavior_id: BEH-181
    title: 'pending text output escapes ESC in a summary as \x1b[2J and never emits a raw ESC byte'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_pending_output_escapes_terminal_controls
  - behavior_id: BEH-182
    title: 'pending still lists the readable entry and exits 0 when pending.jsonl contains rows without kind or severity'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_pending_entry_without_kind_or_severity_is_unreadable
  - behavior_id: BEH-183
    title: 'search --json returns hits whose path ends with the matching regime file'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_search_cli
  - behavior_id: BEH-184
    title: 'search text output escapes ESC and U+202E found in a regime body as \x1b and \u202e'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_search_output_escapes_terminal_controls
  - behavior_id: BEH-185
    title: 'status text mode prints ''pending: N unreadable lines'' when pending.jsonl has corrupt rows'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_pending_skips_unreadable_lines_and_status_counts_them
  - behavior_id: BEH-186
    title: 'pending prints ''no pending changes'' and search prints the ''no hits'' hint on empty results, both exit 0'
    state: proposed
    level: component
    adapter: pytest
---

# status, pending, search: read-only reports with --json raw and text escaped

## What

`status [--json]` prints `status.report()` (profile presence/validity/age, regime counts by applicability, obligation counts, open pending by severity, unreadable pending lines, last check, per-regime problems) either as JSON or via `status.render()`, always exit 0.

`pending [--json]` lists open entries from `pending.jsonl` as JSON or as `id  severity  kind  summary` rows, printing `no pending changes` when empty, exit 0.

`search <query> [-k N] [--kind regime|mirror|profile] [--json]` prints ranked hits as JSON or as `score  kind  path` plus an indented snippet, and `no hits — try the source's own vocabulary` when empty, exit 0.

In text mode every value read from a file (id, severity, kind, summary, path, snippet, problem lines) passes through `render.printable`; `--json` output is `json.dumps(..., indent=2)` with `ensure_ascii` left at its default. Unreadable pending rows are skipped and counted, never fatal, so these commands still run on a poisoned `pending.jsonl`.

## Why

These are the commands an agent runs first (SKILL.md: "read the register before answering"), so they must never refuse on account of a bad row (principle 9) and must never let mirrored or hand-written text repaint the operator's terminal (principle 10, docs-mirror ADR-008).

`--json` exists for the freya integration by file/stdout contract (D2 refined). The "no hits" hint tells an agent to retry with the regulator's vocabulary rather than conclude the obligation is absent (principle 4 in spirit).

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-179 status --json returns a report object with profile.present true and regimes.binds 0 on a fresh project | proposed | `tests/test_cli.py::test_status_json` |
| BEH-180 pending --json lists an added entry and, after resolve, an empty list | proposed | `tests/test_cli.py::test_resolve_and_pending` |
| BEH-181 pending text output escapes ESC in a summary as \x1b[2J and never emits a raw ESC byte | proposed | `tests/test_cli.py::test_pending_output_escapes_terminal_controls` |
| BEH-182 pending still lists the readable entry and exits 0 when pending.jsonl contains rows without kind or severity | proposed | `tests/test_poisoned_files_do_not_brick.py::test_pending_entry_without_kind_or_severity_is_unreadable` |
| BEH-183 search --json returns hits whose path ends with the matching regime file | proposed | `tests/test_cli.py::test_search_cli` |
| BEH-184 search text output escapes ESC and U+202E found in a regime body as \x1b and \u202e | proposed | `tests/test_cli.py::test_search_output_escapes_terminal_controls` |
| BEH-185 status text mode prints 'pending: N unreadable lines' when pending.jsonl has corrupt rows | proposed | `tests/test_poisoned_files_do_not_brick.py::test_pending_skips_unreadable_lines_and_status_counts_them` |
| BEH-186 pending prints 'no pending changes' and search prints the 'no hits' hint on empty results, both exit 0 | proposed | — (test owed) |

## Intentional Design Decisions

### --json output bypasses render.printable

**Decision**: In JSON mode the report is emitted with `json.dumps` and no per-field escaping; only text mode escapes.

**Rationale**: JSON is for a machine consumer that will parse it, and `json.dumps` with the default `ensure_ascii=True` already emits control characters and all non-ASCII as `\uXXXX` escapes, so the terminal never receives a raw ESC or U+202E. Escaping twice would corrupt the payload.

**Security Scan Note**: A scanner flagging "unescaped file content printed in --json mode" should note `ensure_ascii=True` makes the JSON itself ASCII-only and control-free (commit 1033ffb: "--json stays raw").

### status, pending and search always exit 0, even when problems are listed

**Decision**: A profile with problems, regimes with problems or unreadable pending lines are reported inside the output but do not change the exit code.

**Rationale**: These are reports, not validators; the validators (`profile validate`, `regimes validate`, `sources validate`) carry the exit-1 semantics. An agent that wants a gate calls those.

**Security Scan Note**: Not a swallowed error: the problems are printed and the dedicated validate commands exit 1 on the same input.

### Fixed-vocabulary fields (kind, action, score) print without escaping

**Decision**: `h.kind`, `e['action']` and numeric scores are printed raw; only free-text or file-derived strings go through `printable`.

**Rationale**: Those values are constrained to module constants (search kinds, `pending.ACTIONS`) before they reach the CLI, so there is nothing to escape; keeping the call sites minimal keeps the sink rule legible.

**Security Scan Note**: Do not flag as an escape gap: the raw fields cannot contain file content.

## Related Specs

- [SPEC-017: CLI dispatch, exit-code contract and refusal boundary](./SPEC-017-cli-dispatch-exit-codes.md)
- [SPEC-020: resolve: record a named human's decision on a pending entry](./SPEC-020-resolve.md)
- [SPEC-021: Validators: profile validate, regimes validate, sources validate](./SPEC-021-validators.md)
- [SPEC-024: render.printable: escape at the terminal sink](./SPEC-024-render-printable.md)
- [SPEC-003: Pending: append-only pending.jsonl and resolutions.jsonl with replay-derived state](../features/SPEC-003-pending-append-only-logs.md)
- [SPEC-005: Status: counts, profile age and pending totals, never a verdict](../features/SPEC-005-status-counts-never-verdict.md)
- [SPEC-006: Search: BM25 over compliance markdown with a signature-keyed derived index](../features/SPEC-006-search-bm25-signature-index.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan by freya-spec-manager |
