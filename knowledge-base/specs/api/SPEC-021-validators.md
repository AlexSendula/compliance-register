---
id: SPEC-021
title: 'Validators: profile validate, regimes validate, sources validate (exit 1 with problems, network-free)'
category: api
tags: [api, cli, validate, principle-3, principle-9]
status: implemented
certainty: 90
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/cli.py
  - compliance_register/profile.py
  - compliance_register/regimes.py
  - compliance_register/sources.py
  - tests/test_cli.py
intentional_decisions:
  - "Problems go to stdout and the exit code is the only verdict"
  - "Validators never mutate the files they check"
behaviors:
  - behavior_id: BEH-191
    title: 'profile validate on the profile init writes exits 1 and lists unanswered dimensions'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_profile_validate_fails_on_fresh_profile
  - behavior_id: BEH-192
    title: 'sources validate exits 0 on an empty sources.json and exits 1 naming https and adapter problems for an http api-tier source without adapter'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_sources_validate_cli
  - behavior_id: BEH-193
    title: 'profile validate without a profile.md prints ''no profile.md — run init'' to stderr and exits 1'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_profile_validate_without_a_profile_md_prints_no_profile_md_run_init_to_stderr_and_exits_1
  - behavior_id: BEH-194
    title: 'regimes validate exits 1 and prints ''<id>: <problem>'' for a regime whose frontmatter does not parse, while still loading the others'
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_regimes_validate_exits_1_and_prints_id_problem_for_a_regime_whose_frontmatter_does_not_parse_while_still_loading_the_others
---

# Validators: profile validate, regimes validate, sources validate (exit 1 with problems, network-free)

## What

Three subcommands run a module validator and print each problem on its own stdout line, through `printable`, then exit 1 if any problem was found and 0 otherwise.

- `profile validate` loads `profile.md` and runs `profile.validate(meta)`; a missing `profile.md` prints `no profile.md — run init` to stderr and exits 1.
- `regimes validate` loads every regime file and prints `<id>: <problem>` for each parse or shape problem.
- `sources validate` runs `sources.validate()` on every entry in `sources.json` (the same function `check` and `fetch` gate on before their first request) and makes no network call. A corrupt `sources.json` raises `SourcesError`, which `main` turns into exit 1.

## Why

Principle 3: an unconfirmed or malformed entry must not count, and an agent needs a cheap, offline way to find out why `check` or `rescan` would refuse. SKILL.md documents `sources validate` as "check and fetch run this first and make no request while it fails" so the gate is visible and reproducible. Principle 9: problems are listed, not thrown; a bad regime file is reported next to the good ones.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-191 profile validate on the profile init writes exits 1 and lists unanswered dimensions | accepted | `tests/test_cli.py::test_profile_validate_fails_on_fresh_profile` |
| BEH-192 sources validate exits 0 on an empty sources.json and exits 1 naming https and adapter problems for an http api-tier source without adapter | accepted | `tests/test_cli.py::test_sources_validate_cli` |
| BEH-193 profile validate without a profile.md prints 'no profile.md — run init' to stderr and exits 1 | accepted | `tests/test_cli.py::test_profile_validate_without_a_profile_md_prints_no_profile_md_run_init_to_stderr_and_exits_1` |
| BEH-194 regimes validate exits 1 and prints '<id>: <problem>' for a regime whose frontmatter does not parse, while still loading the others | accepted | `tests/test_cli.py::test_regimes_validate_exits_1_and_prints_id_problem_for_a_regime_whose_frontmatter_does_not_parse_while_still_loading_the_others` |

## Intentional Design Decisions

### Problems go to stdout and the exit code is the only verdict

**Decision**: Validation problems are printed on stdout (not stderr) one per line; the command exits 1 when the list is non-empty.

**Rationale**: The list is the payload an agent reads to fix the file; stderr is reserved for "the command itself could not run" (missing profile, refused).

**Security Scan Note**: n/a

### Validators never mutate the files they check

**Decision**: No validator rewrites, normalises or auto-fixes a profile, regime or sources entry.

**Rationale**: Principle 3 and D7: code proposes, humans decide; a validator that "helpfully" fixed a status would be auto-confirming.

**Security Scan Note**: n/a

## Related Specs

- [SPEC-017: CLI dispatch, exit-code contract and refusal boundary](./SPEC-017-cli-dispatch-exit-codes.md)
- [SPEC-025: sources.json model](./SPEC-025-sources-model.md)
- [SPEC-026: sources.validate and refusals](./SPEC-026-sources-validate-refusals.md)
- [SPEC-001: Profile: 15 dimensions, propose/confirm lifecycle, null blocks](../features/SPEC-001-profile-dimensions-propose-confirm.md)
- [SPEC-002: Regimes: one file per regime, frontmatter validation, obligation parsing and counts](../features/SPEC-002-regimes-one-file-per-regime.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan by freya-spec-manager |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
| 2026-09-21 | Tests written for BEH-193, BEH-194; promoted confirmed → accepted | tests owed |
