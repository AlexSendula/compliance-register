---
id: SPEC-015
title: "fetch command: acquire confirmed sources into the mirror"
category: integration
tags: [integration, fetch, mirror, pending, exit-codes]
status: implemented
certainty: 92
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/fetch.py
  - compliance_register/cli.py
  - compliance_register/sources.py
  - compliance_register/pending.py
  - tests/test_fetch.py
  - tests/test_cli.py
intentional_decisions:
  - "last_version advances only when the adapter wrote pages"
  - "Unnamed refuse-tier sources are reported, not an error"
  - "One source-unreachable pending entry per source while one is open"
  - "Any adapter exception becomes a refusal naming the exception type"
behaviors:
  - behavior_id: BEH-144
    title: "a confirmed source is fetched, written pages land under mirror/<jur>/<id>, and last_fetched is set"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_fetch.py::test_fetch_writes_and_updates_source
  - behavior_id: BEH-145
    title: "naming a tier: refuse source lists it as refused and exits 2"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_fetch.py::test_fetch_refuses_refuse_tier
  - behavior_id: BEH-146
    title: "an adapter exception is a refusal naming the exception, the run continues and last_fetched stays None"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_fetch.py::test_adapter_exception_is_refused_and_run_continues
  - behavior_id: BEH-147
    title: "a validation problem exits 2 before any request is made"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_fetch.py::test_validation_problem_exits_2_before_any_request
  - behavior_id: BEH-148
    title: "a named source that is not confirmed is refused with exit 2 and no request"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_fetch.py::test_named_unconfirmed_source_is_refused
  - behavior_id: BEH-149
    title: "a guard refusal exits 1 and writes exactly one source-unreachable info entry with affects, across two runs"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_fetch.py::test_guard_refusal_writes_one_source_unreachable_and_exits_1
  - behavior_id: BEH-150
    title: "fetch --today rejects a non-ISO date with exit 1"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_today_must_be_an_iso_date
  - behavior_id: BEH-151
    title: "--force refetches sources whose version or lastmod is unchanged"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_fetch.py::test_force_refetches_sources_whose_version_or_lastmod_is_unchanged
  - behavior_id: BEH-152
    title: "an unnamed confirmed tier: refuse source is reported in details without changing the exit code"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_fetch.py::test_an_unnamed_confirmed_tier_refuse_source_is_reported_in_details_without_changing_the_exit_code
---

# fetch command: acquire confirmed sources into the mirror

## What

`fetch.run(cdir, ids, force, today, client_factory)` loads sources.json and selects every `confirmed` source (no ids) or the named ids. `sources.refusals` runs before any request: a validation problem, or a named source that is not confirmed, returns exit 2 with the reason per source and makes no network call. `adapters.prefetch` runs once.

In the loop, a `tier: refuse` source is listed as refused with a tier message and forces exit 2 only when it was named explicitly; every other source's adapter `fetch` is called inside a try that turns any exception into a refused FetchResult naming the exception type. Written and skipped counts are summed; a refusal sets exit to at least 1 and appends one `source-unreachable` (severity info) pending entry per source, deduped against open entries, with the affected binds/undetermined regimes. `last_fetched` (and `last_version` when the adapter returned one) are set only when something was written. sources.json is saved after the loop.

The CLI prints `written · skipped · refused` and each detail through `render.printable`, and refuses a non-ISO `--today` with exit 1.

## Why

Principle 3: only confirmed sources are fetched; naming an unconfirmed one is a refusal, not an override. Principle 9 and commit 3b80c26: nothing raises inside the loop so one bad source never aborts the run for the rest and sources.json is always written. D29 exit codes: 1 when a guard or HTTP refused something, 2 when validation failed before any request or a refuse-tier source was requested. Principle 6 / D19 and commit 15960e7: a guard refusal is recorded as a pending entry so it is surfaced, but one open entry per source keeps a daily run from spamming pending.jsonl. Plan B: only fetch writes last_version, and only after every guard passed. Principle 10: every printed detail passes through printable.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-144 a confirmed source is fetched, written pages land under mirror/<jur>/<id>, and last_fetched is set | accepted | `tests/test_fetch.py::test_fetch_writes_and_updates_source` |
| BEH-145 naming a tier: refuse source lists it as refused and exits 2 | accepted | `tests/test_fetch.py::test_fetch_refuses_refuse_tier` |
| BEH-146 an adapter exception is a refusal naming the exception, the run continues and last_fetched stays None | accepted | `tests/test_fetch.py::test_adapter_exception_is_refused_and_run_continues` |
| BEH-147 a validation problem exits 2 before any request is made | accepted | `tests/test_fetch.py::test_validation_problem_exits_2_before_any_request` |
| BEH-148 a named source that is not confirmed is refused with exit 2 and no request | accepted | `tests/test_fetch.py::test_named_unconfirmed_source_is_refused` |
| BEH-149 a guard refusal exits 1 and writes exactly one source-unreachable info entry with affects, across two runs | accepted | `tests/test_fetch.py::test_guard_refusal_writes_one_source_unreachable_and_exits_1` |
| BEH-150 fetch --today rejects a non-ISO date with exit 1 | accepted | `tests/test_cli.py::test_today_must_be_an_iso_date` |
| BEH-151 --force refetches sources whose version or lastmod is unchanged | accepted | `tests/test_fetch.py::test_force_refetches_sources_whose_version_or_lastmod_is_unchanged` |
| BEH-152 an unnamed confirmed tier: refuse source is reported in details without changing the exit code | accepted | `tests/test_fetch.py::test_an_unnamed_confirmed_tier_refuse_source_is_reported_in_details_without_changing_the_exit_code` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### last_version advances only when the adapter wrote pages

**Decision**: `s.last_version = r.version` runs inside `if r.written`; a refused or skipped fetch leaves it untouched.

**Rationale**: Plan B global constraint: check never writes last_version, fetch only after the guards; otherwise a refused version would read as fresh on the next check (principle 4).

**Security Scan Note**: Intended write gating, not a missed update.

### Unnamed refuse-tier sources are reported, not an error

**Decision**: A confirmed `tier: refuse` source is added to refused/details but only sets exit 2 when `--source` named it.

**Rationale**: D24/D29: a refuse-tier source is expected in a register (robots or licence forbid; principle 8); fetching everything must not fail because one is present, but asking for it explicitly is a refusal.

**Security Scan Note**: The asymmetry is the exit-code contract in SKILL.md.

### One source-unreachable pending entry per source while one is open

**Decision**: `fetch.run` reads open (kind, source) pairs first and adds an entry only when none is open, even across guard refusals with different messages.

**Rationale**: Principle 6: record and surface once; a human resolves it. Duplicates per day would be unauditable noise.

**Security Scan Note**: Later refusals with different reasons are visible in the command output but not appended while the first is open — deliberate.

### Any adapter exception becomes a refusal naming the exception type

**Decision**: `except Exception` around the adapter call yields `FetchResult(refused=['RuntimeError: …'])`.

**Rationale**: Principle 9: the failure mode must be "it told me", and the run must continue to save sources.json.

**Security Scan Note**: Broad except at the loop boundary; the type and message are preserved in details and in the pending summary.

## Related Specs

- [SPEC-007: HTTP client](./SPEC-007-http-client.md)
- [SPEC-009: Mirror store](./SPEC-009-mirror-store.md)
- [SPEC-010: Adapter contract, registry and shared guards](./SPEC-010-adapter-contract.md)
- [SPEC-014: EUR-Lex adapter](./SPEC-014-eurlex-adapter.md)
- [SPEC-016: check command](./SPEC-016-check-command.md)
- [SPEC-003: Pending: append-only pending.jsonl and resolutions.jsonl with replay-derived state](../features/SPEC-003-pending-append-only-logs.md)
- [SPEC-023: Watch commands at the CLI: fetch, check, rescan — exit relay, --today injection, text summaries](../api/SPEC-023-watch-commands-cli.md)
- [SPEC-026: sources.validate and refusals: the network-free gate before any request](../api/SPEC-026-sources-validate-refusals.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Inferred from code, tests and design repo (D19, D24, D29); certainty 92 |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
| 2026-09-21 | Tests written for BEH-151, BEH-152; promoted confirmed → accepted | tests owed |
