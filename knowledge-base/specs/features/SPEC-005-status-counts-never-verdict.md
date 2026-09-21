---
id: SPEC-005
title: "Status: counts, profile age and pending totals, never a verdict"
category: features
tags: [status, report, counts, router-not-oracle, D1, D15]
status: implemented
certainty: 91
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/status.py
  - compliance_register/profile.py
  - compliance_register/regimes.py
  - compliance_register/pending.py
  - compliance_register/render.py
  - compliance_register/cli.py
  - tests/test_status.py
  - tests/test_cli.py
  - tests/test_poisoned_files_do_not_brick.py
intentional_decisions:
  - "The report never contains a verdict"
  - "status exits 0 even when problems exist"
  - "Unclear obligations are counted, not listed"
  - "A non-ISO confirmed_at yields no age, not an error"
behaviors:
  - behavior_id: BEH-043
    title: "report on an empty compliance dir yields profile absent, zero regimes, zero open pending and last_check None"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_status.py::test_report_on_empty_project
  - behavior_id: BEH-044
    title: "report computes age_days from confirmed_at vs today, per-severity pending counts and reads .last-check; render contains no 'compliant' and no unclear obligation ids"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_status.py::test_report_full
  - behavior_id: BEH-045
    title: "a confirmed_at that is not an ISO date gives age_days None and renders 'not yet confirmed' without raising"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_status.py::test_non_iso_confirmed_at_is_no_age_not_a_traceback
  - behavior_id: BEH-046
    title: "unreadable pending lines are reported in pending.unreadable and rendered as 'pending: N unreadable lines'"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_pending_skips_unreadable_lines_and_status_counts_them
  - behavior_id: BEH-047
    title: "regime problems appear in report.problems as '<id>: <problem>' and are rendered through printable"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_regime_with_wrong_shaped_sources_and_applies_is_reported_not_fatal
  - behavior_id: BEH-048
    title: "`status --json` exits 0 and prints the report as JSON"
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_status_json
  - behavior_id: BEH-049
    title: "the 'pending: N unreadable lines' line is omitted when there are no unreadable lines"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-283
    title: "an unreadable profile.md is reported as a profile problem and rendered, never an abort"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_status.py::test_corrupt_profile_is_a_problem_not_an_abort
---

# Status: counts, profile age and pending totals, never a verdict

## What

`status.report(cdir, today)` assembles one dict: `profile` (`present`, the `validate` problem list — which starts with `unreadable: …` when `profile.md` cannot be parsed, rendered as extra `profile: …` lines — `confirmed_at`, and `age_days` computed from `confirmed_at` against `today`, or `None` when the date is missing or not ISO), `regimes` (the six `regimes.counts` totals), `pending` (`open`, a per-severity breakdown over major/minor/info, and the `unreadable` line count across both logs), `last_check` (the contents of `.last-check` or `None`) and `problems` (`<id>: <problem>` for every regime problem).

`render(rep)` prints a fixed set of lines: the profile line (`none — run the profile stage first`, or `valid`/`N problem(s)` with `N days old`/`not yet confirmed`), the regimes line, the obligations line with the unclear count, the pending line with severities, an extra `pending: N unreadable lines` line only when N > 0, `last check: <ts|never>`, and one `problem: …` line per regime problem passed through `render.printable`. The CLI's `status [--json]` always exits 0.

## Why

The register is a router, not an oracle (Principle 1, D1 as reframed by D15): it reports counts of regimes and obligations and never "checked" or "compliant", so the report is deliberately a denominator and nothing else. Unclear obligations are counted rather than listed because status is a one-screen summary; the detail lives in the regime file and in `regimes validate`.

The profile age is surfaced so a stale profile is visible without any timer (Principle 5, D14 reframed as a reminder). A hand-written `confirmed_at` that is not a date yields no age instead of a traceback because a bad file must never prevent a command from running (Principle 9). Regime problem strings originate in human-edited files and pass through `printable` on the way to the terminal (Principle 10).

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-043 report on an empty compliance dir yields profile absent, zero regimes, zero open pending and last_check None | proposed | `tests/test_status.py::test_report_on_empty_project` |
| BEH-044 report computes age_days from confirmed_at vs today, per-severity pending counts and reads .last-check; render contains no 'compliant' and no unclear obligation ids | proposed | `tests/test_status.py::test_report_full` |
| BEH-045 a confirmed_at that is not an ISO date gives age_days None and renders 'not yet confirmed' without raising | proposed | `tests/test_status.py::test_non_iso_confirmed_at_is_no_age_not_a_traceback` |
| BEH-046 unreadable pending lines are reported in pending.unreadable and rendered as 'pending: N unreadable lines' | proposed | `tests/test_poisoned_files_do_not_brick.py::test_pending_skips_unreadable_lines_and_status_counts_them` |
| BEH-047 regime problems appear in report.problems as '<id>: <problem>' and are rendered through printable | proposed | `tests/test_poisoned_files_do_not_brick.py::test_regime_with_wrong_shaped_sources_and_applies_is_reported_not_fatal` |
| BEH-048 `status --json` exits 0 and prints the report as JSON | proposed | `tests/test_cli.py::test_status_json` |
| BEH-049 the 'pending: N unreadable lines' line is omitted when there are no unreadable lines | proposed | — (test owed) |
| BEH-283 an unreadable profile.md is reported as a profile problem and rendered, never an abort | proposed | `tests/test_status.py::test_corrupt_profile_is_a_problem_not_an_abort` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### The report never contains a verdict

**Decision**: `report` returns counts and problem lists only; `render` never emits the words "compliant" or "checked" and never scores anything.

**Rationale**: Router, not oracle (Principle 1; D1, D15). A register that also judges compliance becomes the thing people trust instead of checking.

**Security Scan Note**: Absence of any pass/fail or coverage percentage is by design, not a missing feature.

### status exits 0 even when problems exist

**Decision**: `cmd_status` returns 0 regardless of profile problems, regime problems or unreadable lines; the gates with a non-zero exit are `profile validate`, `regimes validate` and `rescan`.

**Rationale**: status is a report a human reads or a script parses with `--json`; failing it would make the tool brick on the very files it is meant to describe (Principle 9).

**Security Scan Note**: Not a missed error path; the problem list is in the output for callers that want to act on it.

### Unclear obligations are counted, not listed

**Decision**: `render` prints `N unclear` and never the unclear obligation ids; tests assert the id of an unclear obligation is absent from the output.

**Rationale**: Status is a summary line per concern; listing per-obligation detail would turn it into a checklist, which D15 rules out.

**Security Scan Note**: The omission is intentional.

### A non-ISO confirmed_at yields no age, not an error

**Decision**: `_age_days` catches `ValueError` from `date.fromisoformat` and returns `None`; render then says `not yet confirmed`.

**Rationale**: A hand-written value like "soon" is a data problem the profile validator does not own; the report must still render (Principle 9).

**Security Scan Note**: The swallowed ValueError is deliberate and bounded to the age computation.

## Related Specs

- [SPEC-001: Profile: 15 dimensions, propose/confirm lifecycle, null blocks](./SPEC-001-profile-dimensions-propose-confirm.md) — source of the profile problem list and `confirmed_at`
- [SPEC-002: Regimes: one file per regime, frontmatter validation, obligation parsing and counts](./SPEC-002-regimes-one-file-per-regime.md) — source of `counts` and per-regime problems
- [SPEC-003: Pending: append-only pending.jsonl and resolutions.jsonl](./SPEC-003-pending-append-only-logs.md) — source of `list_open` and `unreadable`
- [SPEC-019: status, pending, search: read-only reports with --json raw and text escaped](../api/SPEC-019-status-pending-search.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan; certainty 91 |
| 2026-09-21 | `profile.load` absorbs an unreadable file into `Profile.problems`; status reports and renders it; BEH-283 added | G2 principle checkpoint, principle 9 |
