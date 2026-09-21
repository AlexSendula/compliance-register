---
id: SPEC-016
title: "check command: three-valued freshness, pending entries, date-passed and profile-stale"
category: integration
tags: [integration, check, watch, freshness, pending, exit-codes]
status: implemented
certainty: 93
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/check.py
  - compliance_register/fetch.py
  - compliance_register/pending.py
  - compliance_register/regimes.py
  - compliance_register/profile.py
  - compliance_register/cli.py
  - tests/test_check.py
  - tests/test_poisoned_files_do_not_brick.py
  - tests/test_cli.py
intentional_decisions:
  - "check never writes last_version"
  - "An HttpRefused (robots, DTD, budget, policy) inside check is reported as unreachable, never fresh"
  - "Every move is recorded as severity major"
  - "Only binds and undetermined regimes are watched"
  - "changed is truncated to 20 entries in the pending row, with changed_total carrying the real count"
  - "Nothing-to-check still runs the date-passed pass"
behaviors:
  - behavior_id: BEH-153
    title: "a moved source yields one source-moved entry with affects and source, last_status moved, last_version None, and .last-check dated today"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_check_records_moved_with_affects
  - behavior_id: BEH-154
    title: "an unreachable source yields a source-unreachable info entry and last_status unreachable, never fresh"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_check_unreachable_is_info_never_fresh
  - behavior_id: BEH-155
    title: "profile-stale is added once across two runs after a move"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_check_adds_profile_stale_once
  - behavior_id: BEH-156
    title: "an adapter exception is unreachable naming the exception and the next source is still checked"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_adapter_exception_is_unreachable_and_run_continues
  - behavior_id: BEH-157
    title: "a validation problem exits 2 before any request with no pending entry and no .last-check"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_validation_problem_exits_2_before_any_request
  - behavior_id: BEH-158
    title: "a named unconfirmed source is refused with exit 2 and no request"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_named_unconfirmed_source_is_refused
  - behavior_id: BEH-159
    title: "an open source-moved entry is not duplicated by a second run"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_moved_entry_is_not_duplicated_while_open
  - behavior_id: BEH-160
    title: "source-next is recorded once per (source, to) and next_version is stored on the source"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_source_next_recorded_once_and_on_source
  - behavior_id: BEH-161
    title: "date-passed is emitted once per watched regime whose review_by has arrived, not for future or no-longer-applies regimes"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_date_passed_for_review_by_once
  - behavior_id: BEH-162
    title: "with no confirmed sources check exits 2 and still emits date-passed"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_date_passed_runs_even_with_nothing_to_check
  - behavior_id: BEH-163
    title: "_affects lists only binds/undetermined regimes referencing the source"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_affects_skips_ruled_out_and_no_longer_applies
  - behavior_id: BEH-164
    title: "exit is 1 when any source was unreachable and 0 when sources only moved"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_unreachable_source_exits_1
  - behavior_id: BEH-165
    title: "a regime with wrong-shaped sources/applies does not break _affects or the run"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_regime_with_wrong_shaped_sources_and_applies_is_reported_not_fatal
  - behavior_id: BEH-166
    title: "check --today rejects a non-ISO date with exit 1"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_today_must_be_an_iso_date
  - behavior_id: BEH-167
    title: "check --json prints the report as JSON with the three counts and details"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_check_json_prints_the_report_as_json_with_the_three_counts_and_details
  - behavior_id: BEH-168
    title: "a tier: refuse source is silently excluded from selection and does not affect the exit code"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_a_tier_refuse_source_is_silently_excluded_from_selection_and_does_not_affect_the_exit_code
  - behavior_id: BEH-284
    title: "an unreadable profile.md becomes a detail line and never denies the check report"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_corrupt_profile_does_not_deny_the_check_report
  - behavior_id: BEH-286
    title: "a moved row truncated to 20 changed URLs records the full count in changed_total"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_moved_row_records_the_full_changed_count_when_truncated
---

# check command: three-valued freshness, pending entries, date-passed and profile-stale

## What

`check.run(cdir, ids, today, client_factory)` selects confirmed (or named) sources whose tier is not `refuse`. With nothing to check it exits 2, still runs the date-passed pass, and returns. `sources.refusals` runs before any request; a problem exits 2 with nothing written (no pending entry, no `.last-check`).

After one `adapters.prefetch`, each source's adapter `check` is called inside a try; any exception becomes an unreachable CheckResult naming the exception. Counters fresh/moved/unreachable are incremented from the status; a `moved` result appends a `source-moved` (major) entry with from/to/changed[:20] and the affected binds/undetermined regimes unless one is open for the same (source, to); `unreachable` appends `source-unreachable` (info) unless one is open for the source; a returned next_version appends `source-next` (info) once per (source, to) and is stored on the source. `last_checked` and `last_status` are written per source; `last_version` never. Exit is 1 when any source was unreachable, else 0 (moved is 0).

Afterwards sources.json is saved, `date-passed` (major) is appended once per binds/undetermined regime whose review_by <= today, `.last-check` is written with a UTC timestamp, and one `profile-stale` (info) entry is appended when something moved, a profile exists, none is already open, and the profile's confirmed_at is missing or earlier than today.

The CLI prints the three counts and details through printable, `--json` dumps the report, and a non-ISO `--today` exits 1.

## Why

Principle 4: freshness is exactly fresh/unreachable/moved and a failed fetch is never reported as absence or as fresh. Principle 5 / D16: check is a command with no schedule. Principle 6 / D19: it appends to pending.jsonl and stops; commit 726b55a dedupes so a daily run with an unresolved move does not add a row per day. D26: every move is major; triage happens at resolve. D14 reframed: profile-stale is a reminder, not a gate. Commit bb5b41c: date-passed runs even with nothing to check because review_by is the only signal for a refuse-tier source (D24). Principle 9 and commit 3b80c26: nothing raises inside the loop so `.last-check` and sources.json are always written. D29: exit 1 when at least one source was unreachable; exit 2 for nothing to check or validation before network. Plan B: check never writes last_version. Principle 10: every printed detail passes through printable.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-153 a moved source yields one source-moved entry with affects and source, last_status moved, last_version None, and .last-check dated today | accepted | `tests/test_check.py::test_check_records_moved_with_affects` |
| BEH-154 an unreachable source yields a source-unreachable info entry and last_status unreachable, never fresh | accepted | `tests/test_check.py::test_check_unreachable_is_info_never_fresh` |
| BEH-155 profile-stale is added once across two runs after a move | accepted | `tests/test_check.py::test_check_adds_profile_stale_once` |
| BEH-156 an adapter exception is unreachable naming the exception and the next source is still checked | accepted | `tests/test_check.py::test_adapter_exception_is_unreachable_and_run_continues` |
| BEH-157 a validation problem exits 2 before any request with no pending entry and no .last-check | accepted | `tests/test_check.py::test_validation_problem_exits_2_before_any_request` |
| BEH-158 a named unconfirmed source is refused with exit 2 and no request | accepted | `tests/test_check.py::test_named_unconfirmed_source_is_refused` |
| BEH-159 an open source-moved entry is not duplicated by a second run | accepted | `tests/test_check.py::test_moved_entry_is_not_duplicated_while_open` |
| BEH-160 source-next is recorded once per (source, to) and next_version is stored on the source | accepted | `tests/test_check.py::test_source_next_recorded_once_and_on_source` |
| BEH-161 date-passed is emitted once per watched regime whose review_by has arrived, not for future or no-longer-applies regimes | accepted | `tests/test_check.py::test_date_passed_for_review_by_once` |
| BEH-162 with no confirmed sources check exits 2 and still emits date-passed | accepted | `tests/test_check.py::test_date_passed_runs_even_with_nothing_to_check` |
| BEH-163 _affects lists only binds/undetermined regimes referencing the source | accepted | `tests/test_check.py::test_affects_skips_ruled_out_and_no_longer_applies` |
| BEH-164 exit is 1 when any source was unreachable and 0 when sources only moved | accepted | `tests/test_check.py::test_unreachable_source_exits_1` |
| BEH-165 a regime with wrong-shaped sources/applies does not break _affects or the run | accepted | `tests/test_poisoned_files_do_not_brick.py::test_regime_with_wrong_shaped_sources_and_applies_is_reported_not_fatal` |
| BEH-166 check --today rejects a non-ISO date with exit 1 | accepted | `tests/test_cli.py::test_today_must_be_an_iso_date` |
| BEH-167 check --json prints the report as JSON with the three counts and details | accepted | `tests/test_cli.py::test_check_json_prints_the_report_as_json_with_the_three_counts_and_details` |
| BEH-168 a tier: refuse source is silently excluded from selection and does not affect the exit code | accepted | `tests/test_check.py::test_a_tier_refuse_source_is_silently_excluded_from_selection_and_does_not_affect_the_exit_code` |
| BEH-284 an unreadable profile.md becomes a detail line and never denies the check report | accepted | `tests/test_check.py::test_corrupt_profile_does_not_deny_the_check_report` |
| BEH-286 a moved row truncated to 20 changed URLs records the full count in changed_total | accepted | `tests/test_check.py::test_moved_row_records_the_full_changed_count_when_truncated` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### check never writes last_version

**Decision**: Only `last_checked`, `last_status` and `next_version` are written per source; the moved entry records `to` but the source keeps its old version until fetch succeeds.

**Rationale**: Plan B global constraint: advancing the version on check would make the next check read fresh with nothing mirrored (principle 4).

**Security Scan Note**: Intended: a moved source stays moved until fetch passes its guards.

### An HttpRefused (robots, DTD, budget, policy) inside check is reported as unreachable, never fresh

**Decision**: Adapters catch HttpRefused alongside HttpUnreachable and return status unreachable; check exits 1.

**Rationale**: Principle 4: the three-valued result has no "refused" arm; the detail string names the reason and the tool told the human (principle 9).

**Security Scan Note**: A refusal counted as "unreachable" is deliberate folding, not a misclassification; the detail is exact.

### Every move is recorded as severity major

**Decision**: `source-moved` entries are always "major"; `source-unreachable`, `source-next` and `profile-stale` are "info".

**Rationale**: D26: major/minor is a triage label set by the human at resolve; the engine does not judge the change (principle 6: record, surface, delegate).

**Security Scan Note**: Not a missing severity heuristic.

### Only binds and undetermined regimes are watched

**Decision**: `_affects` and `_date_passed` skip regimes with status ruled-out or no-longer-applies.

**Rationale**: A ruled-out regime's sources moving is not actionable; principle 1 — the register reports what applies.

**Security Scan Note**: Intended filter.

### changed is truncated to 20 entries in the pending row, with changed_total carrying the real count

**Decision**: A `source-moved` row stores at most the first 20 changed URLs under `changed` and the full count under `changed_total`, so a reader can tell the list was cut.

**Rationale**: A sitemap move can list 2000 URLs; the full list is in the command output and the mirror manifest.

**Security Scan Note**: Deliberate bound on pending.jsonl row size.

### Nothing-to-check still runs the date-passed pass

**Decision**: The exit-2 early return happens after `_date_passed`.

**Rationale**: For a refuse-tier source, review_by is the only watch signal (D24, commit bb5b41c).

**Security Scan Note**: A write on an exit-2 path is intentional here and limited to date-passed.

## Related Specs

- [SPEC-007: HTTP client](./SPEC-007-http-client.md)
- [SPEC-010: Adapter contract, registry and shared guards](./SPEC-010-adapter-contract.md)
- [SPEC-011: Sitemap adapter](./SPEC-011-sitemap-adapter.md)
- [SPEC-012: Feed adapter](./SPEC-012-feed-adapter.md)
- [SPEC-013: Page-hash adapter](./SPEC-013-pagehash-adapter.md)
- [SPEC-014: EUR-Lex adapter](./SPEC-014-eurlex-adapter.md)
- [SPEC-015: fetch command](./SPEC-015-fetch-command.md)
- [SPEC-001: Profile: 15 dimensions, propose/confirm lifecycle, null blocks](../features/SPEC-001-profile-dimensions-propose-confirm.md)
- [SPEC-002: Regimes: one file per regime, frontmatter validation, obligation parsing and counts](../features/SPEC-002-regimes-one-file-per-regime.md)
- [SPEC-003: Pending: append-only pending.jsonl and resolutions.jsonl with replay-derived state](../features/SPEC-003-pending-append-only-logs.md)
- [SPEC-023: Watch commands at the CLI: fetch, check, rescan — exit relay, --today injection, text summaries](../api/SPEC-023-watch-commands-cli.md)
- [SPEC-026: sources.validate and refusals: the network-free gate before any request](../api/SPEC-026-sources-validate-refusals.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Inferred from code, tests and design repo (D14, D16, D19, D24, D26, D29); certainty 93 |
| 2026-09-20 | profile-stale requires a profile and is deduped against an open entry | Cross-check against `check.run` |
| 2026-09-21 | An unreadable profile.md is a `details['profile.md']` line, not an abort; BEH-284 added | G2 principle checkpoint, principle 9 |
| 2026-09-21 | `changed_total` added beside the truncated `changed` list; BEH-286 added | G3 contradiction check, principle 9 |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
| 2026-09-21 | Tests written for BEH-167, BEH-168; promoted confirmed → accepted | tests owed |
