---
id: SPEC-004
title: "Rescan: confirmed-answer snapshot, drift detection and regime-new/regime-gone entries"
category: features
tags: [rescan, profile-snapshot, drift, pending, incremental, D7, D18, D19]
status: implemented
certainty: 91
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/rescan.py
  - compliance_register/profile.py
  - compliance_register/regimes.py
  - compliance_register/pending.py
  - compliance_register/cli.py
  - tests/test_rescan.py
  - tests/test_cli.py
  - tests/test_poisoned_files_do_not_brick.py
intentional_decisions:
  - "Snapshot holds confirmed answers only"
  - "First run writes the snapshot and reports nothing"
  - "Rescan writes pending entries and never edits a regime file"
  - "Only binds and undetermined regimes get regime-gone"
  - "An invalid profile is refused before any write"
behaviors:
  - behavior_id: BEH-033
    title: "the first rescan writes profile.snapshot.json and reports zero entries"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_rescan.py::test_first_rescan_snapshots_without_entries
  - behavior_id: BEH-034
    title: "a confirmed dimension that becomes falsy raises regime-gone (major) for each binds/undetermined regime whose applies.triggered_by names it"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_rescan.py::test_removed_trigger_marks_regime_gone
  - behavior_id: BEH-035
    title: "a confirmed dimension that gains or changes a value raises one regime-new (info) entry naming the dimension"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_rescan.py::test_new_answer_asks_for_discover
  - behavior_id: BEH-036
    title: "a proposed answer is stored as null in the snapshot, and confirming it later is reported as a change"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_rescan.py::test_snapshot_holds_only_confirmed_values
  - behavior_id: BEH-037
    title: "an invalid profile returns exit 2 with the problems and writes no snapshot"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_rescan.py::test_invalid_profile_is_refused_with_exit_2
  - behavior_id: BEH-038
    title: "`rescan` on a fresh profile exits 2 and names the unanswered dimensions on stderr"
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_rescan_cli_exits_2_on_invalid_profile
  - behavior_id: BEH-039
    title: "a regime whose applies is not a mapping does not break rescan; the drift is still reported"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_regime_with_wrong_shaped_sources_and_applies_is_reported_not_fatal
  - behavior_id: BEH-040
    title: "run returns error 'no profile.md' when the profile is absent"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-041
    title: "ruled-out and no-longer-applies regimes never receive a regime-gone entry"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-042
    title: "`--today` must be YYYY-MM-DD; any other string exits 1"
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_today_must_be_an_iso_date
  - behavior_id: BEH-281
    title: "a corrupt profile.snapshot.json is refused by name with exit 1 and the baseline is left untouched"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_rescan.py::test_corrupt_snapshot_is_refused_with_a_message
  - behavior_id: BEH-282
    title: "an unreadable profile.md is refused with exit 2 and the problem named"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_rescan.py::test_corrupt_profile_is_refused_with_a_message
---
# Rescan: confirmed-answer snapshot, drift detection and regime-new/regime-gone entries
## What
`rescan.run(cdir, *, today)` compares the profile's confirmed answers with `profile.snapshot.json`, the baseline the previous run wrote. It returns `{changed: [], entries: 0, error: 'no profile.md'}` without a profile, and `{…, error: 'profile does not validate: …', exit: 2}` without writing anything when `profile.validate` reports problems (an unreadable `profile.md` surfaces there as `unreadable: …`). A `profile.snapshot.json` that cannot be parsed returns `{…, error: 'profile.snapshot.json is unreadable: …', exit: 1}` and is never overwritten — the baseline is refused by name, not silently reset.
The current baseline is built from the 15 dimensions with a value only where `status == 'confirmed'`; a `proposed` or `unanswered` answer contributes `null`. On the first run (no snapshot) the current baseline is treated as the previous one, so nothing is reported and the snapshot is written.
Otherwise, for each dimension whose value differs: if the new value is null, False, empty list/dict or empty string, every regime with status `binds` or `undetermined` whose `applies.triggered_by` names that dimension gets a `regime-gone` entry (severity major, `affects=[regime]`); else one `regime-new` entry (severity info) is written naming the dimension and, if any, the regimes it touches. `triggered_by` may be a list of `{dim: value}` mappings or `dim: value` strings; only the dimension keys matter.
The snapshot is rewritten at the end as sorted, indented JSON. Regime files are never modified. The CLI's `rescan [--today YYYY-MM-DD]` prints the error to stderr and returns the reported exit code (2 for an invalid profile), or prints `changed: … · pending entries written: N`.
## Why
Rescan must look only at what changed since last time (D18): the diff against a committed snapshot makes each run incremental and lets the team share the same baseline. Only confirmed answers count because code proposes and humans decide (D7, Principle 3): a proposed value must not advance the baseline, and confirming it later is itself the change that triggers discovery. The first run reporting nothing is the consequence of having no baseline, not a bug.
A lost trigger produces a major `regime-gone` entry instead of touching the regime file because nothing in the register moves until a human resolves the entry (D19, Principle 6); the resolver re-runs stage 2b and sets `no-longer-applies`. Ruled-out and no-longer-applies regimes are not disturbed because their status already records that they do not bind. An invalid profile is refused with exit 2 before the snapshot is written (D29) so a half-filled profile can never become the baseline.
## Behavior
The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.
| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-033 the first rescan writes profile.snapshot.json and reports zero entries | proposed | `tests/test_rescan.py::test_first_rescan_snapshots_without_entries` |
| BEH-034 a confirmed dimension that becomes falsy raises regime-gone (major) for each binds/undetermined regime whose applies.triggered_by names it | proposed | `tests/test_rescan.py::test_removed_trigger_marks_regime_gone` |
| BEH-035 a confirmed dimension that gains or changes a value raises one regime-new (info) entry naming the dimension | proposed | `tests/test_rescan.py::test_new_answer_asks_for_discover` |
| BEH-036 a proposed answer is stored as null in the snapshot, and confirming it later is reported as a change | proposed | `tests/test_rescan.py::test_snapshot_holds_only_confirmed_values` |
| BEH-037 an invalid profile returns exit 2 with the problems and writes no snapshot | proposed | `tests/test_rescan.py::test_invalid_profile_is_refused_with_exit_2` |
| BEH-038 `rescan` on a fresh profile exits 2 and names the unanswered dimensions on stderr | proposed | `tests/test_cli.py::test_rescan_cli_exits_2_on_invalid_profile` |
| BEH-039 a regime whose applies is not a mapping does not break rescan; the drift is still reported | proposed | `tests/test_poisoned_files_do_not_brick.py::test_regime_with_wrong_shaped_sources_and_applies_is_reported_not_fatal` |
| BEH-040 run returns error 'no profile.md' when the profile is absent | proposed | — (test owed) |
| BEH-041 ruled-out and no-longer-applies regimes never receive a regime-gone entry | proposed | — (test owed) |
| BEH-042 `--today` must be YYYY-MM-DD; any other string exits 1 | proposed | `tests/test_cli.py::test_today_must_be_an_iso_date` |
| BEH-281 a corrupt profile.snapshot.json is refused by name with exit 1 and the baseline is left untouched | proposed | `tests/test_rescan.py::test_corrupt_snapshot_is_refused_with_a_message` |
| BEH-282 an unreadable profile.md is refused with exit 2 and the problem named | proposed | `tests/test_rescan.py::test_corrupt_profile_is_refused_with_a_message` |
Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.
## Intentional Design Decisions
### Snapshot holds confirmed answers only
**Decision**: A dimension whose status is `proposed` or `unanswered` is recorded as `null` in profile.snapshot.json regardless of its value.
**Rationale**: Code proposes, never decides (D7, Principle 3). A proposed value must not advance the baseline; confirming it later is the change rescan should notice.
**Security Scan Note**: Values present in profile.md but absent from the snapshot are dropped on purpose; this is not data loss.
### First run writes the snapshot and reports nothing
**Decision**: When no snapshot exists, `previous = current`, so `changed` is empty and no pending entry is written.
**Rationale**: There is nothing to diff against; inventing a "regime-new" for every dimension would flood pending.jsonl with noise on day one.
**Security Scan Note**: Zero entries on a first run is expected.
### Rescan writes pending entries and never edits a regime file
**Decision**: A lost trigger yields a `regime-gone` entry (major) naming the regime; the status change to `no-longer-applies` is left to whoever resolves the entry.
**Rationale**: Record, surface, delegate (D19, Principle 6). Auto-flipping a regime's status would be an unaudited change to the register.
**Security Scan Note**: The absence of any write to regimes/ is intentional; do not flag as an incomplete update.
### Only binds and undetermined regimes get regime-gone
**Decision**: A regime with status `ruled-out` or `no-longer-applies` is skipped even if its `triggered_by` names the lost dimension.
**Rationale**: Those statuses already record that the regime does not bind; a gone entry for them would ask the human to confirm a fact already confirmed.
**Security Scan Note**: Intentional filter, not a missed case.
### An invalid profile is refused before any write
**Decision**: `run` returns `exit: 2` with the validation problems and does not create or update the snapshot.
**Rationale**: Refused, not failed (D29, Principle 9): validation failed before any state moved, and a partially confirmed profile must never become the baseline that later runs diff against.
**Security Scan Note**: Exit 2 with no side effects is the specified behaviour.
## Related Specs
- [SPEC-001: Profile: 15 dimensions, propose/confirm lifecycle, null blocks](./SPEC-001-profile-dimensions-propose-confirm.md) — supplies `validate` and the confirmed-status semantics the snapshot keys on
- [SPEC-002: Regimes: one file per regime, frontmatter validation, obligation parsing and counts](./SPEC-002-regimes-one-file-per-regime.md) — supplies `applies.triggered_by` and the status filter
- [SPEC-003: Pending: append-only pending.jsonl and resolutions.jsonl](./SPEC-003-pending-append-only-logs.md) — the only sink rescan writes to
- [SPEC-023: Watch commands at the CLI: fetch, check, rescan — exit relay, --today injection, text summaries](../api/SPEC-023-watch-commands-cli.md)
## Change History
| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan; certainty 91 |
| 2026-09-21 | A corrupt snapshot is refused by name (exit 1) instead of raising; an unreadable profile.md is refused through `validate` (exit 2); BEH-281, BEH-282 added | G2 principle checkpoint, principle 9 |
