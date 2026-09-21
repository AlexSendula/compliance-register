---
id: SPEC-001
title: "Profile: 15 dimensions, propose/confirm lifecycle, null blocks"
category: features
tags: [profile, dimensions, frontmatter, validation, human-confirmation, D7, D8]
status: implemented
certainty: 93
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/profile.py
  - compliance_register/frontmatter.py
  - compliance_register/cli.py
  - references/dimensions-checklist.md
  - references/method-profile.md
  - tests/test_profile.py
  - tests/test_cli.py
intentional_decisions:
  - "No code path confirms a profile answer"
  - "validate reports, it does not raise"
  - "diff compares values only, not status or evidence"
  - "Unknown answer keys are problems, not ignored"
  - "git ref for profile diff is passed after --end-of-options"
behaviors:
  - behavior_id: BEH-001
    title: "DIMENSIONS is exactly 15 slugs with establishment first, directed_activity second and time_change last"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_profile.py::test_dimensions_are_fifteen_and_ordered
  - behavior_id: BEH-002
    title: "empty() seeds every dimension as status unanswered with value null and no evidence"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_profile.py::test_empty_has_every_dimension_unanswered
  - behavior_id: BEH-003
    title: "validate reports each unanswered dimension and each confirmed answer whose value is null"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_profile.py::test_validate_flags_missing_and_null
  - behavior_id: BEH-004
    title: "validate returns no problems when all 15 are confirmed with values and confirmed_by/confirmed_at are set"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_profile.py::test_validate_ok
  - behavior_id: BEH-005
    title: "validate rejects an answer whose status is not one of unanswered/proposed/confirmed and a key that is not a known dimension"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_profile.py::test_validate_rejects_an_answer_whose_status_is_not_one_of_unanswered_proposed_confirmed_and_a_key_that_is_not_a_known_dimension
  - behavior_id: BEH-006
    title: "validate requires confirmed_by and confirmed_at only once every answer is confirmed"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_profile.py::test_validate_requires_confirmed_by_and_confirmed_at_only_once_every_answer_is_confirmed
  - behavior_id: BEH-007
    title: "diff lists the dimensions whose value changed, in dimension order"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_profile.py::test_diff_lists_changed_dimensions
  - behavior_id: BEH-008
    title: "load returns None when profile.md is absent and a Profile with meta and body when present"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_profile.py::test_load_reads_file
  - behavior_id: BEH-009
    title: "`profile validate` on a freshly initialised profile exits 1 and prints the unanswered dimensions"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_profile_validate_fails_on_fresh_profile
  - behavior_id: BEH-010
    title: "`profile diff --against <file>` prints only the changed slugs and exits 0"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_profile_diff_against_file
  - behavior_id: BEH-011
    title: "`profile diff --against <ref>` invokes git show with --end-of-options so the ref is never parsed as a git option"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_profile_diff_ref_is_never_a_git_option
---

# Profile: 15 dimensions, propose/confirm lifecycle, null blocks

## What

profile.py owns `knowledge-base/compliance/profile.md`: a YAML-frontmatter file holding exactly the 15 dimension answers from references/dimensions-checklist.md, in a fixed order with `establishment` and `directed_activity` first and `time_change` last. Each answer is `{value, status, evidence[]}` with status in `unanswered | proposed | confirmed`; `empty()` seeds every dimension as unanswered with a null value and no evidence.

`validate(meta)` returns a list of problem strings rather than raising: every unanswered dimension, every confirmed answer whose value is null, any status outside the three, any missing dimension, any key that is not one of the 15, and, once all 15 are confirmed, a missing `confirmed_by` or `confirmed_at`. `diff(old, new)` returns the dimension slugs whose `value` differs, in dimension order, ignoring status and evidence. `load(cdir)` returns `None` when the file is absent, a `Profile(meta, body, path)` otherwise, and — when the file cannot be read or parsed — a `Profile` with empty `meta` and `problems=['unreadable: …']`, which `validate(meta, problems)` returns as-is so every caller refuses or reports by name instead of raising (principle 9).

The CLI exposes `profile validate` (exit 1 when any problem is printed) and `profile diff --against <file|git-ref>`, where a non-file argument is passed to `git show --end-of-options <ref>:<path>`. No function in the module ever writes `status: confirmed`, `confirmed_by` or `confirmed_at`.

## Why

The checklist is the one fixed artifact the skill ships (D5, Principle 2): questions, not answers, so the slug tuple is the schema and everything else is per-project data. Code may propose an answer from repository evidence but a human confirms every field and `null` blocks (D7, Principle 3), which is why `validate` treats both `unanswered` and `confirmed`-with-null as problems and why no code path confirms.

Questions 1 and 2 are ordered first because they choose which jurisdictions' sources are read (D8). `validate` reports instead of raising so `status` can show a half-filled profile without failing, while `rescan` uses the same list to refuse with exit 2 (D29). `diff` is value-only because its purpose is to answer "what changed since <ref>" for a human, not to track the confirm transition; the confirmed-only baseline is rescan's job.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-001 DIMENSIONS is exactly 15 slugs with establishment first, directed_activity second and time_change last | accepted | `tests/test_profile.py::test_dimensions_are_fifteen_and_ordered` |
| BEH-002 empty() seeds every dimension as status unanswered with value null and no evidence | accepted | `tests/test_profile.py::test_empty_has_every_dimension_unanswered` |
| BEH-003 validate reports each unanswered dimension and each confirmed answer whose value is null | accepted | `tests/test_profile.py::test_validate_flags_missing_and_null` |
| BEH-004 validate returns no problems when all 15 are confirmed with values and confirmed_by/confirmed_at are set | accepted | `tests/test_profile.py::test_validate_ok` |
| BEH-005 validate rejects an answer whose status is not one of unanswered/proposed/confirmed and a key that is not a known dimension | accepted | `tests/test_profile.py::test_validate_rejects_an_answer_whose_status_is_not_one_of_unanswered_proposed_confirmed_and_a_key_that_is_not_a_known_dimension` |
| BEH-006 validate requires confirmed_by and confirmed_at only once every answer is confirmed | accepted | `tests/test_profile.py::test_validate_requires_confirmed_by_and_confirmed_at_only_once_every_answer_is_confirmed` |
| BEH-007 diff lists the dimensions whose value changed, in dimension order | accepted | `tests/test_profile.py::test_diff_lists_changed_dimensions` |
| BEH-008 load returns None when profile.md is absent and a Profile with meta and body when present | accepted | `tests/test_profile.py::test_load_reads_file` |
| BEH-009 `profile validate` on a freshly initialised profile exits 1 and prints the unanswered dimensions | accepted | `tests/test_cli.py::test_profile_validate_fails_on_fresh_profile` |
| BEH-010 `profile diff --against <file>` prints only the changed slugs and exits 0 | accepted | `tests/test_cli.py::test_profile_diff_against_file` |
| BEH-011 `profile diff --against <ref>` invokes git show with --end-of-options so the ref is never parsed as a git option | accepted | `tests/test_cli.py::test_profile_diff_ref_is_never_a_git_option` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### No code path confirms a profile answer

**Decision**: profile.py has no function that sets `status: confirmed`, `confirmed_by` or `confirmed_at`; `validate` lists every unanswered dimension and every confirmed answer with a null value as a problem.

**Rationale**: Code proposes, humans decide; `null` blocks (D7, Principle 3). SKILL.md instructs agents to "Propose, show, wait." An unconfirmed inference presented as fact is worse than no entry.

**Security Scan Note**: The absence of a confirm/auto-fill helper and the "confirmed but value is null" problem are intentional. Do not flag as a missing feature or as an incomplete validation path.

### validate reports, it does not raise

**Decision**: `validate(meta, problems=None)` returns a list of strings; it never raises, and `load` never raises either — an unreadable file becomes `Profile.problems`, which `validate` passes through untouched. Only the CLI (`profile validate`) and `rescan` turn the list into a non-zero exit.

**Rationale**: `status` must be able to describe an in-progress profile (Principle 9: refuse loudly, never brick). The gate lives where it matters: `rescan` refuses an invalid profile with exit 2 before advancing any baseline.

**Security Scan Note**: A scanner may flag that invalid profiles are "accepted" by `load`. Validation is applied by every consumer that mutates state; `load` is deliberately permissive.

### diff compares values only, not status or evidence

**Decision**: `diff(old, new)` lists a dimension only when its `value` differs; a proposed→confirmed transition with the same value is not reported.

**Rationale**: `profile diff` answers "what answer changed since this commit" for a human reviewer. The confirmed-only baseline that matters for regimes lives in `profile.snapshot.json` and is handled by `rescan` (see SPEC-004).

**Security Scan Note**: Not a missed comparison; the confirm transition is tracked by rescan's snapshot, not by diff.

### Unknown answer keys are problems, not ignored

**Decision**: Any key under `answers` that is not one of the 15 slugs yields `<key>: not a known dimension`.

**Rationale**: A misspelled slug would otherwise silently leave the real dimension unanswered while looking answered; strict keys keep the file and the checklist in lockstep (D5).

**Security Scan Note**: Strict schema on a human-edited file is intentional; do not recommend tolerating extra keys.

### git ref for profile diff is passed after --end-of-options

**Decision**: `_profile_meta_from` tries the argument as a file path first; otherwise runs `git show --end-of-options <ref>:<relpath>` with `capture_output=True`, so a ref beginning with `-` cannot become a git option.

**Rationale**: `--against` is user input that reaches a subprocess; the guard makes `--against=--output=/tmp/x` a bad revision rather than a file write.

**Security Scan Note**: Subprocess with user input is guarded by `--end-of-options` and list-form argv (no shell). Covered by tests/test_cli.py::test_profile_diff_ref_is_never_a_git_option.

## Related Specs

- [SPEC-004: Rescan: confirmed-answer snapshot, drift detection and regime-new/regime-gone entries](./SPEC-004-rescan-snapshot-drift.md) — consumes `validate` and the confirmed-only baseline
- [SPEC-005: Status: counts, profile age and pending totals, never a verdict](./SPEC-005-status-counts-never-verdict.md) — reports the `validate` problem list and `confirmed_at` age
- [SPEC-006: Search: BM25 over compliance markdown](./SPEC-006-search-bm25-signature-index.md) — indexes `profile.md` as kind `profile`
- [SPEC-021: Validators: profile validate, regimes validate, sources validate (exit 1 with problems, network-free)](../api/SPEC-021-validators.md)
- [SPEC-022: profile diff --against <file or git ref> with --end-of-options](../api/SPEC-022-profile-diff.md)
- [SPEC-023: Watch commands at the CLI: fetch, check, rescan — exit relay, --today injection, text summaries](../api/SPEC-023-watch-commands-cli.md)
- [SPEC-029: Frontmatter: YAML block read/write, atomic save, ISO date normalisation](../infra/SPEC-029-frontmatter-yaml-atomic-save-date-normalisation.md)
- [SPEC-031: Shipped references: method files, regime template, dimensions checklist and SPARQL template carry the method, never the law](../infra/SPEC-031-shipped-references-method-never-law.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan; certainty 93 |
| 2026-09-21 | `load` absorbs an unreadable profile.md into `Profile.problems`; `validate` takes them through | P4b drift check after f34d2fa |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
| 2026-09-21 | Tests written for BEH-005, BEH-006; promoted confirmed → accepted | tests owed |
