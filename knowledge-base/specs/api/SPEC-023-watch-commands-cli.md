---
id: SPEC-023
title: 'Watch commands at the CLI: fetch, check, rescan — exit relay, --today injection, text summaries'
category: api
tags: [api, cli, fetch, check, rescan, D16, D29, principle-4, principle-5]
status: implemented
certainty: 91
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/cli.py
  - compliance_register/fetch.py
  - compliance_register/check.py
  - compliance_register/rescan.py
  - tests/test_cli.py
  - tests/test_check.py
  - tests/test_fetch.py
  - tests/test_rescan.py
intentional_decisions:
  - "--today must be a strict ISO date; any other spelling is exit 1"
  - "The CLI relays the module's exit code and never derives one from stdout"
  - "No timer, cron, --watch or --interval flag exists"
  - "An unreachable source is exit 1 and is never reported as fresh"
behaviors:
  - behavior_id: BEH-199
    title: 'check, fetch and rescan reject --today values that are not YYYY-MM-DD with exit 1 and a message containing YYYY-MM-DD'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_today_must_be_an_iso_date
  - behavior_id: BEH-200
    title: 'rescan on a profile that does not validate prints the reasons to stderr and exits 2'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_rescan_cli_exits_2_on_invalid_profile
  - behavior_id: BEH-201
    title: 'check on a corrupt sources.json exits 1 with the file name in stderr'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_corrupt_sources_json_is_a_typed_error_and_exit_1
  - behavior_id: BEH-202
    title: 'check exits 2 and makes no request when a chosen source fails validation'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_validation_problem_exits_2_before_any_request
  - behavior_id: BEH-203
    title: 'check exits 1 when at least one source is unreachable and 0 when every source is fresh or moved'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_check.py::test_unreachable_source_exits_1
  - behavior_id: BEH-204
    title: 'fetch exits 2 when a refuse-tier source is named with --source'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_fetch.py::test_fetch_refuses_refuse_tier
  - behavior_id: BEH-205
    title: 'fetch exits 1 and writes one source-unreachable entry when a guard refuses a page'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_fetch.py::test_guard_refusal_writes_one_source_unreachable_and_exits_1
  - behavior_id: BEH-206
    title: 'check text output ends with ''see: compliance-register pending'' only when moved or unreachable is non-zero'
    state: confirmed
    level: component
    adapter: pytest
---

# Watch commands at the CLI: fetch, check, rescan — exit relay, --today injection, text summaries

## What

`fetch [--source ID]... [--force] [--today DATE]`, `check [--source ID]... [--json] [--today DATE]` and `rescan [--today DATE]` call the corresponding module `run()` and return its `exit` field; the CLI never recomputes the code.

`--today` is validated by `_iso_date` as a strict `YYYY-MM-DD` date (argparse type error, exit 1) and defaults to today's local date; it is threaded into every written date.

- `fetch` prints `written N · skipped N · refused N` and one `  <id>: <detail>` line per source.
- `check` prints `fresh N · moved N · unreachable N`, per-source detail, and `see: compliance-register pending` when anything moved or was unreachable; `--json` dumps the report.
- `rescan` prints `changed: a, b · pending entries written: N` on success; on an error dict it prints the error to stderr and returns the report's exit (2 for an invalid profile, 1 for no profile).

Per D29 the codes mean: `check` 0 all fresh/moved, 1 at least one unreachable, 2 nothing to check or validation failed; `fetch` 0 done, 1 a guard or HTTP refused something, 2 a refuse-tier source named, validation failed or a named source unconfirmed; `rescan` 0 done, 1 no profile, 2 invalid profile.

## Why

D16 / principle 5: the skill exposes commands and the caller decides when to run them; there is no scheduler, timer or `--watch`. D29 gives each outcome a code so an agent can branch on it without parsing text.

`--today` is injectable because the date is written into `sources.json`, `.last-check` and pending entries and compared as a string against `review_by` (commit 93caebf); tests must not depend on the wall clock (principle 11) and a non-ISO value would silently break the string comparison. The `see: compliance-register pending` hint enforces principle 6: `check` records and surfaces, a human resolves.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-199 check, fetch and rescan reject --today values that are not YYYY-MM-DD with exit 1 and a message containing YYYY-MM-DD | accepted | `tests/test_cli.py::test_today_must_be_an_iso_date` |
| BEH-200 rescan on a profile that does not validate prints the reasons to stderr and exits 2 | accepted | `tests/test_cli.py::test_rescan_cli_exits_2_on_invalid_profile` |
| BEH-201 check on a corrupt sources.json exits 1 with the file name in stderr | accepted | `tests/test_poisoned_files_do_not_brick.py::test_corrupt_sources_json_is_a_typed_error_and_exit_1` |
| BEH-202 check exits 2 and makes no request when a chosen source fails validation | accepted | `tests/test_check.py::test_validation_problem_exits_2_before_any_request` |
| BEH-203 check exits 1 when at least one source is unreachable and 0 when every source is fresh or moved | accepted | `tests/test_check.py::test_unreachable_source_exits_1` |
| BEH-204 fetch exits 2 when a refuse-tier source is named with --source | accepted | `tests/test_fetch.py::test_fetch_refuses_refuse_tier` |
| BEH-205 fetch exits 1 and writes one source-unreachable entry when a guard refuses a page | accepted | `tests/test_fetch.py::test_guard_refusal_writes_one_source_unreachable_and_exits_1` |
| BEH-206 check text output ends with 'see: compliance-register pending' only when moved or unreachable is non-zero | confirmed | — (test owed) |

## Intentional Design Decisions

### --today must be a strict ISO date; any other spelling is exit 1

**Decision**: `_iso_date` accepts only what `date.fromisoformat` parses and re-serialises, so `tomorrow`, `2026-13-40` and `20260920` are rejected before the command runs.

**Rationale**: The value is stored verbatim and compared lexicographically with `review_by` dates; a different format would compare wrongly and silently. Refusing is cheaper than a wrong date-passed decision.

**Security Scan Note**: Clock injection via a flag is intended (deterministic tests, backfilling a check date); it is not a time-of-check weakness.

### The CLI relays the module's exit code and never derives one from stdout

**Decision**: `cmd_fetch`/`cmd_check` return `rep['exit']`; `cmd_rescan` returns `rep.get('exit', 1)` on error and 0 otherwise.

**Rationale**: Exit semantics are decided next to the logic that knows whether a request was made (D29 distinguishes "ran but unreachable" from "refused before any request"); the CLI is I/O only.

**Security Scan Note**: n/a

### No timer, cron, --watch or --interval flag exists

**Decision**: The command surface offers `check` and `rescan` only; there is nothing that schedules them.

**Rationale**: D16 and principle 5: commands, not schedules. When they run is the project's decision.

**Security Scan Note**: A "no background refresh" observation is by design, not a missing feature.

### An unreachable source is exit 1 and is never reported as fresh

**Decision**: `check` counts unreachable separately and exits 1 when any source could not be told; it does not downgrade to 0 or upgrade to moved.

**Rationale**: Principle 4: "could not reach" is never "not there". The pending entry is severity `info` so the human sees it without it looking like a legal change.

**Security Scan Note**: n/a

## Related Specs

- [SPEC-017: CLI dispatch, exit-code contract and refusal boundary](./SPEC-017-cli-dispatch-exit-codes.md)
- [SPEC-025: sources.json model](./SPEC-025-sources-model.md)
- [SPEC-026: sources.validate and refusals](./SPEC-026-sources-validate-refusals.md)
- [SPEC-004: Rescan: confirmed-answer snapshot, drift detection and regime-new/regime-gone entries](../features/SPEC-004-rescan-snapshot-drift.md)
- [SPEC-015: fetch command: acquire confirmed sources into the mirror](../integration/SPEC-015-fetch-command.md)
- [SPEC-016: check command: three-valued freshness, pending entries, date-passed and profile-stale](../integration/SPEC-016-check-command.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan by freya-spec-manager |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
