---
id: SPEC-020
title: 'resolve: record a named human''s decision on a pending entry'
category: api
tags: [api, cli, resolve, pending, D19, D26, principle-6, principle-3]
status: implemented
certainty: 90
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/cli.py
  - compliance_register/pending.py
  - tests/test_cli.py
intentional_decisions:
  - "--by is mandatory; there is no anonymous or automatic resolution"
  - "Resolving never edits pending.jsonl; state is derived by replaying resolutions.jsonl"
  - "Unknown id is exit 1 (bad input), not exit 2 (refused)"
behaviors:
  - behavior_id: BEH-187
    title: 'resolve <id> --action applied --by <name> --note <text> exits 0 and the entry no longer appears in pending --json'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_resolve_and_pending
  - behavior_id: BEH-188
    title: "resolve with an id that is not in pending.jsonl prints 'unknown pending id' to stderr and exits 1"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_resolve_with_an_id_that_is_not_open_prints_unknown_pending_id_to_stderr_and_exits_1
  - behavior_id: BEH-189
    title: 'resolve without --by, or with an action outside applied/dismissed/deferred, is an argparse error and exits 1'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_resolve_without_by_or_with_an_action_outside_applied_dismissed_deferred_is_an_argparse_error_and_exits_1
  - behavior_id: BEH-190
    title: 'The success line prints the id and the --by name through printable'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_the_success_line_prints_the_id_and_the_by_name_through_printable
---

# resolve: record a named human's decision on a pending entry

## What

`resolve <id> --action applied|dismissed|deferred --by <name> [--note TEXT]` calls `pending.resolve()`, which appends one row to `resolutions.jsonl`; the entry then disappears from `pending` because open state is derived by replay.

`--action` is restricted by argparse to `pending.ACTIONS` and `--by` is required, so a call without a named person is a usage error (exit 1) before any file is touched. An id that is not an open pending entry is `unknown pending id: <id>` on stderr with exit 1; a `ValueError` from `pending` (e.g. already resolved) is printed and exits 1. On success it prints `<id> <action> by <name>` and exits 0. The id and the name are passed through `printable` when printed; the action is one of the fixed choices.

## Why

D19 and principle 6: record, surface, delegate. Nothing in the register moves until a human resolves the entry, and the log must show who did what. D26 makes major/minor a triage label applied at resolve time by the human or the assessing agent. Append-only resolutions (principle 6, D26) keep both files readable top to bottom without wondering what was edited.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-187 resolve <id> --action applied --by <name> --note <text> exits 0 and the entry no longer appears in pending --json | accepted | `tests/test_cli.py::test_resolve_and_pending` |
| BEH-188 resolve with an id that is not in pending.jsonl prints 'unknown pending id' to stderr and exits 1 | accepted | `tests/test_cli.py::test_resolve_with_an_id_that_is_not_open_prints_unknown_pending_id_to_stderr_and_exits_1` |
| BEH-189 resolve without --by, or with an action outside applied/dismissed/deferred, is an argparse error and exits 1 | accepted | `tests/test_cli.py::test_resolve_without_by_or_with_an_action_outside_applied_dismissed_deferred_is_an_argparse_error_and_exits_1` |
| BEH-190 The success line prints the id and the --by name through printable | accepted | `tests/test_cli.py::test_the_success_line_prints_the_id_and_the_by_name_through_printable` |

## Intentional Design Decisions

### --by is mandatory; there is no anonymous or automatic resolution

**Decision**: argparse requires `--by`; the CLI offers no flag that resolves entries in bulk or without a name.

**Rationale**: Principle 3 and D19: code proposes, humans decide, and the audit trail must name the human. An unattributed resolution would be unauditable.

**Security Scan Note**: The name is free text and is not verified against git identity; that is deliberate (the skill has no identity system). It is escaped on output.

### Resolving never edits pending.jsonl; state is derived by replaying resolutions.jsonl

**Decision**: `resolve` appends to `resolutions.jsonl` and leaves `pending.jsonl` untouched.

**Rationale**: Principle 6: logs are append-only. A reviewer can diff either file in git and see every event.

**Security Scan Note**: A scanner expecting the `status` field in `pending.jsonl` to flip should not report a stale-state bug.

### Unknown id is exit 1 (bad input), not exit 2 (refused)

**Decision**: `KeyError` from `pending.resolve` maps to exit 1.

**Rationale**: D29: a mistyped id is bad input; 2 is reserved for the tool declining to act on valid input.

**Security Scan Note**: n/a

## Related Specs

- [SPEC-017: CLI dispatch, exit-code contract and refusal boundary](./SPEC-017-cli-dispatch-exit-codes.md)
- [SPEC-019: status, pending, search: read-only reports](./SPEC-019-status-pending-search.md)
- [SPEC-003: Pending: append-only pending.jsonl and resolutions.jsonl with replay-derived state](../features/SPEC-003-pending-append-only-logs.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan by freya-spec-manager |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
| 2026-09-21 | Tests written for BEH-188, BEH-189, BEH-190; promoted confirmed → accepted (BEH-188 retitled to the unknown-id case its test pins; the already-resolved case is BEH-025) | tests owed |
