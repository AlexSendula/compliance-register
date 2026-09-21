---
id: SPEC-003
title: "Pending: append-only pending.jsonl and resolutions.jsonl with replay-derived state"
category: features
tags: [pending, resolutions, jsonl, append-only, record-surface-delegate, D19, D26]
status: implemented
certainty: 93
created: 2026-09-20
updated: 2026-09-20
related_code:
  - compliance_register/pending.py
  - compliance_register/cli.py
  - compliance_register/check.py
  - compliance_register/rescan.py
  - tests/test_pending.py
  - tests/test_poisoned_files_do_not_brick.py
  - tests/test_cli.py
intentional_decisions:
  - "Both logs are append-only; there is no edit or delete"
  - "Ids continue from the max id seen, not from line count"
  - "Unreadable rows are skipped and counted, never fatal"
  - "extra cannot override base fields"
  - "Severity is not editable at resolve"
behaviors:
  - behavior_id: BEH-023
    title: "add assigns sequential chg-NNNN ids and appends one JSON line per entry with affects and source"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_pending.py::test_add_assigns_sequential_ids
  - behavior_id: BEH-024
    title: "list_open excludes entries that have a row in resolutions.jsonl, and resolve appends {id, resolved, by, action, note}"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_pending.py::test_list_open_excludes_resolved
  - behavior_id: BEH-025
    title: "resolving an already-resolved id raises ValueError"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_pending.py::test_resolve_twice_fails
  - behavior_id: BEH-026
    title: "add rejects a kind outside KINDS (and a severity outside SEVERITIES) with ValueError"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_pending.py::test_unknown_kind_rejected
  - behavior_id: BEH-027
    title: "the next id continues from the maximum id across both files, so a hand-deleted resolved line never frees its id"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_pending.py::test_ids_continue_from_max_id_not_line_count
  - behavior_id: BEH-028
    title: "a non-JSON line or a row without an id is skipped, counted by unreadable(), and surfaced by status"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_pending_skips_unreadable_lines_and_status_counts_them
  - behavior_id: BEH-029
    title: "a pending row without a string kind and severity is unreadable, and `pending` still lists the good rows"
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_pending_entry_without_kind_or_severity_is_unreadable
  - behavior_id: BEH-030
    title: "resolve raises KeyError for an id that is not in pending.jsonl"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-031
    title: "`resolve <id> --action applied --by X` exits 0 and the id disappears from `pending --json`"
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_resolve_and_pending
  - behavior_id: BEH-032
    title: "`pending` output passes every field through render.printable so ESC and bidi controls are escaped"
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_pending_output_escapes_terminal_controls
---

# Pending: append-only pending.jsonl and resolutions.jsonl with replay-derived state

## What

pending.py is the only writer of `knowledge-base/compliance/pending.jsonl` and `resolutions.jsonl`.

`add(cdir, kind, severity, summary, *, source, affects, extra, now)` validates `kind` against seven kinds (`source-moved, source-unreachable, source-next, regime-new, regime-gone, date-passed, profile-stale`) and `severity` against `major | minor | info`, assigns the next id as `chg-NNNN` from the maximum id seen across both files, appends one JSON line `{id, detected, kind, severity, source, affects, summary, status: 'pending', …extra}` and returns it; `extra` keys may not override the base keys.

`list_open` returns pending rows whose id has no row in resolutions.jsonl. `resolve(cdir, id, action, by, note, now)` validates `action` against `applied | dismissed | deferred`, raises `KeyError` for an unknown id and `ValueError` for an already-resolved one, then appends `{id, resolved, by, action, note}`.

Reading skips blank lines; a line that is not JSON, not an object, lacks an `id`, or (in pending.jsonl) lacks a string `kind` and `severity` is skipped and counted, and `unreadable(cdir)` reports the total for both files. Nothing in the module rewrites, reorders or deletes a line. The CLI's `pending` lists open rows (escaped through `render.printable`) and `resolve <id> --action --by [--note]` exits 1 on KeyError/ValueError.

## Why

Record, surface, delegate (D19, Principle 6): detected changes are written down and stop there, and who resolves them is the caller's process, so the store must be a log a human can read top to bottom and never wonder what was edited. Two append-only files with state derived by replay make every resolution auditable and every change to a compliance register reviewable in git.

Ids continue from the maximum id rather than the line count so a hand-deleted line can never free an id and make a new entry appear pre-resolved. Severity is a triage label recorded by the engine; a downgrade is expressed by the human's action and note at resolve, never by editing the row (D26).

Unreadable rows are skipped and counted, never raised, because one poisoned line must not deny `status`, `pending`, `resolve` or `check` (Principle 9); the shape gate on `kind`/`severity` exists because check, fetch and the CLI index on those two fields.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-023 add assigns sequential chg-NNNN ids and appends one JSON line per entry with affects and source | proposed | `tests/test_pending.py::test_add_assigns_sequential_ids` |
| BEH-024 list_open excludes entries that have a row in resolutions.jsonl, and resolve appends {id, resolved, by, action, note} | proposed | `tests/test_pending.py::test_list_open_excludes_resolved` |
| BEH-025 resolving an already-resolved id raises ValueError | proposed | `tests/test_pending.py::test_resolve_twice_fails` |
| BEH-026 add rejects a kind outside KINDS (and a severity outside SEVERITIES) with ValueError | proposed | `tests/test_pending.py::test_unknown_kind_rejected` |
| BEH-027 the next id continues from the maximum id across both files, so a hand-deleted resolved line never frees its id | proposed | `tests/test_pending.py::test_ids_continue_from_max_id_not_line_count` |
| BEH-028 a non-JSON line or a row without an id is skipped, counted by unreadable(), and surfaced by status | proposed | `tests/test_poisoned_files_do_not_brick.py::test_pending_skips_unreadable_lines_and_status_counts_them` |
| BEH-029 a pending row without a string kind and severity is unreadable, and `pending` still lists the good rows | proposed | `tests/test_poisoned_files_do_not_brick.py::test_pending_entry_without_kind_or_severity_is_unreadable` |
| BEH-030 resolve raises KeyError for an id that is not in pending.jsonl | proposed | — (test owed) |
| BEH-031 `resolve <id> --action applied --by X` exits 0 and the id disappears from `pending --json` | proposed | `tests/test_cli.py::test_resolve_and_pending` |
| BEH-032 `pending` output passes every field through render.printable so ESC and bidi controls are escaped | proposed | `tests/test_cli.py::test_pending_output_escapes_terminal_controls` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### Both logs are append-only; there is no edit or delete

**Decision**: `_append` opens in mode `a`; no function rewrites pending.jsonl or resolutions.jsonl, and resolving adds a row to the second file rather than mutating the first. There is no CLI command to remove or purge entries.

**Rationale**: Auto-applied or edited changes to a compliance register are unauditable (Principle 6, D19). State is replayed from both files so the history is the record.

**Security Scan Note**: Unbounded growth and the lack of a delete path are intentional. The `status: 'pending'` field on a row never changes; open-ness is derived from resolutions.jsonl.

### Ids continue from the max id seen, not from line count

**Decision**: `add` computes the next id as `max(int(id[4:]) over both files) + 1`, including resolved ids.

**Rationale**: If a resolved line is hand-deleted from pending.jsonl, its id must stay burned; otherwise the next entry would inherit an existing resolution and be born resolved.

**Security Scan Note**: Gaps in the chg-NNNN sequence are expected, not evidence of tampering.

### Unreadable rows are skipped and counted, never fatal

**Decision**: `_read` swallows `ValueError` from `json.loads` and drops non-object rows, rows without an `id`, and pending rows without string `kind` and `severity`, incrementing a counter that `status` renders as `pending: N unreadable lines`.

**Rationale**: One corrupt line must not deny every command to the honest rest (Principle 9); the count keeps the failure loud.

**Security Scan Note**: The bare `except ValueError` and the silent drop are deliberate; the loss is surfaced through `unreadable()` and rendered by `status` (SPEC-005).

### extra cannot override base fields

**Decision**: `entry.update({k: v for k, v in extra.items() if k not in entry})` — a caller's `extra` may add fields (`from`, `to`, `effective`) but never replace `id`, `status`, `kind`, `severity`, `detected`, `source`, `affects` or `summary`.

**Rationale**: Adapters supply `extra`; the row's identity and classification must come from the engine.

**Security Scan Note**: Not a dropped-data bug: colliding keys are intentionally ignored.

### Severity is not editable at resolve

**Decision**: `resolve` records only `{id, resolved, by, action, note}`; a row's `severity` is never changed.

**Rationale**: Major/minor is a triage label set by the engine; the human's assessment is expressed as `dismissed`/`deferred` plus a note (D26).

**Security Scan Note**: Absence of a severity-update path is intentional.

## Related Specs

- [SPEC-002: Regimes: one file per regime, frontmatter validation, obligation parsing and counts](./SPEC-002-regimes-one-file-per-regime.md) — `affects` entries name regime ids
- [SPEC-004: Rescan: confirmed-answer snapshot, drift detection and regime-new/regime-gone entries](./SPEC-004-rescan-snapshot-drift.md) — writes `regime-new` / `regime-gone` entries through `add`
- [SPEC-005: Status: counts, profile age and pending totals, never a verdict](./SPEC-005-status-counts-never-verdict.md) — reports `list_open` and `unreadable` totals
- [SPEC-015: fetch command: acquire confirmed sources into the mirror](../integration/SPEC-015-fetch-command.md)
- [SPEC-016: check command: three-valued freshness, pending entries, date-passed and profile-stale](../integration/SPEC-016-check-command.md)
- [SPEC-019: status, pending, search: read-only reports with --json raw and text escaped](../api/SPEC-019-status-pending-search.md)
- [SPEC-020: resolve: record a named human's decision on a pending entry](../api/SPEC-020-resolve.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan; certainty 93 |
