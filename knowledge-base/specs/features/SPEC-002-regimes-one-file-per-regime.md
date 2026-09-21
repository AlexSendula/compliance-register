---
id: SPEC-002
title: "Regimes: one file per regime, frontmatter validation, obligation parsing and counts"
category: features
tags: [regimes, obligations, frontmatter, validation, three-valued-applicability, D13, D22]
status: implemented
certainty: 91
created: 2026-09-20
updated: 2026-09-20
related_code:
  - compliance_register/regimes.py
  - compliance_register/frontmatter.py
  - compliance_register/cli.py
  - references/regime-template.md
  - references/method-register.md
  - tests/test_regimes.py
  - tests/test_poisoned_files_do_not_brick.py
intentional_decisions:
  - "An unreadable regime file is reported, not fatal"
  - "unclear obligations are counted, not rejected"
  - "ruled-out regimes must have a reason and no obligations; binds regimes must quote and cite"
  - "Filename must equal the frontmatter id"
  - "Unknown statuses are loaded but not counted"
behaviors:
  - behavior_id: BEH-012
    title: "load_all parses `### ID · title` headings and `- **Key:** value` bullets into obligations with id, title and fields"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_regimes.py::test_load_all_parses_obligations
  - behavior_id: BEH-013
    title: "validate reports each missing required key and a status outside the four allowed values"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_regimes.py::test_validate_requires_fields
  - behavior_id: BEH-014
    title: "validate requires exempt.reason and forbids obligations when status is ruled-out"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_regimes.py::test_validate_ruled_out_needs_reason_and_no_obligations
  - behavior_id: BEH-015
    title: "validate requires applies.quote and applies.cite when status is binds"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-016
    title: "validate reports duplicate obligation ids and bullet keys outside the six known ones"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-017
    title: "counts returns per-status totals plus obligations and obligations_unclear (missing You must or It says)"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_regimes.py::test_counts
  - behavior_id: BEH-018
    title: "a file whose stem differs from its frontmatter id gets a filename problem"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_regimes.py::test_filename_must_match_id
  - behavior_id: BEH-019
    title: "a regime file with unterminated or invalid frontmatter becomes a placeholder row with an unreadable problem while sibling files load normally"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_regime_with_bad_frontmatter_is_reported_not_fatal
  - behavior_id: BEH-020
    title: "a regime whose sources, applies or exempt are not the expected shape is reported as problems and still counted"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_regime_with_wrong_shaped_sources_and_applies_is_reported_not_fatal
  - behavior_id: BEH-021
    title: "load_all returns an empty list when regimes/ does not exist"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-022
    title: "`regimes validate` prints `<id>: <problem>` lines and exits 1 when any regime has problems"
    state: proposed
    level: component
    adapter: pytest
---

# Regimes: one file per regime, frontmatter validation, obligation parsing and counts

## What

regimes.py reads `knowledge-base/compliance/regimes/*.md`, one file per regime, with status in `binds | ruled-out | undetermined | no-longer-applies` and required frontmatter `id, title, status, jurisdiction, sources, confirmed_by, confirmed_at`.

`parse_obligations(body)` scans the markdown for `### <ID> · <title>` headings (a `-` separator is also accepted; the id charset is `[A-Za-z0-9][A-Za-z0-9._-]*`) and collects the `- **Key:** value` bullets under each into `Obligation.fields`; an obligation is `unclear` when it lacks `You must` or `It says`.

`validate(meta, body)` returns problem strings for: each missing required key, a status outside the four, `sources` not a list of dicts with an `id`, `applies`/`exempt` not mappings, a `binds` regime without `applies.quote` and `applies.cite`, a `ruled-out` regime without `exempt.reason` or with any obligation, duplicate obligation ids, and obligation bullet keys outside the six known ones.

`load_all(cdir)` returns `[]` without a regimes directory, otherwise one `Regime` per file in sorted order; a file whose frontmatter cannot be read becomes a `Regime` with empty status, no obligations and a single `unreadable: …` problem, and a file whose stem differs from its `id` gets a problem. `counts(rs)` returns the four status totals plus `obligations` and `obligations_unclear`, ignoring regimes whose status is not one of the four. The CLI's `regimes validate` prints `<id>: <problem>` lines and exits 1 if any exist.

## Why

The register format is D22: one human-readable, diffable markdown file per regime, including ruled-out ones with their reason, because "the ruled-out list with reasons is the completeness artifact" (D13). A `binds` regime must quote and cite the clause that makes it apply and a `ruled-out` one must give a reason and carry no obligations, because every entry is derived, cited and confirmed (Principle 3) and "If a regime file has no quote, it is not done" (SKILL.md).

`unclear` is a count rather than a validation failure because workflow.md defines it as the register's own denominator ("obligations unclear: no quote, or no action") that status reports without a verdict (D1 reframed). One unreadable file is reported per-row instead of raised so that status, check and rescan keep working for the honest rest (Principle 9). The six bullet keys are fixed so the parser and the template cannot drift apart.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-012 load_all parses `### ID · title` headings and `- **Key:** value` bullets into obligations with id, title and fields | proposed | `tests/test_regimes.py::test_load_all_parses_obligations` |
| BEH-013 validate reports each missing required key and a status outside the four allowed values | proposed | `tests/test_regimes.py::test_validate_requires_fields` |
| BEH-014 validate requires exempt.reason and forbids obligations when status is ruled-out | proposed | `tests/test_regimes.py::test_validate_ruled_out_needs_reason_and_no_obligations` |
| BEH-015 validate requires applies.quote and applies.cite when status is binds | proposed | — (test owed) |
| BEH-016 validate reports duplicate obligation ids and bullet keys outside the six known ones | proposed | — (test owed) |
| BEH-017 counts returns per-status totals plus obligations and obligations_unclear (missing You must or It says) | proposed | `tests/test_regimes.py::test_counts` |
| BEH-018 a file whose stem differs from its frontmatter id gets a filename problem | proposed | `tests/test_regimes.py::test_filename_must_match_id` |
| BEH-019 a regime file with unterminated or invalid frontmatter becomes a placeholder row with an unreadable problem while sibling files load normally | proposed | `tests/test_poisoned_files_do_not_brick.py::test_regime_with_bad_frontmatter_is_reported_not_fatal` |
| BEH-020 a regime whose sources, applies or exempt are not the expected shape is reported as problems and still counted | proposed | `tests/test_poisoned_files_do_not_brick.py::test_regime_with_wrong_shaped_sources_and_applies_is_reported_not_fatal` |
| BEH-021 load_all returns an empty list when regimes/ does not exist | proposed | — (test owed) |
| BEH-022 `regimes validate` prints `<id>: <problem>` lines and exits 1 when any regime has problems | proposed | — (test owed) |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### An unreadable regime file is reported, not fatal

**Decision**: `load_all` catches `FrontmatterError`, `OSError` and `UnicodeDecodeError` per file and emits a placeholder `Regime(status='', problems=['unreadable: …'])`, continuing with the other files.

**Rationale**: One corrupt file must not deny status/check/rescan to the rest (Principle 9, docs-mirror SEC-049/050 shape). The problem row still surfaces in `status` and `regimes validate`.

**Security Scan Note**: The broad per-file except is deliberate. Do not flag as swallowed exceptions; the failure is surfaced as a problem string on the row.

### unclear obligations are counted, not rejected

**Decision**: An obligation missing `You must` or `It says` makes `Obligation.unclear` true and increments `obligations_unclear`; `validate` does not list it as a problem, so a regime with unclear obligations still validates.

**Rationale**: An in-progress register is legal; the count is the register's honesty signal (workflow.md "Counts the register reports", D1 reframed by D15). Blocking would turn the register into a gate, which D15 rules out.

**Security Scan Note**: Not an incomplete validation rule. The unclear count is surfaced by `status` (SPEC-005).

### ruled-out regimes must have a reason and no obligations; binds regimes must quote and cite

**Decision**: `validate` adds `exempt.reason: required when status is ruled-out`, `obligations: a ruled-out regime must not list obligations`, and `applies: quote and cite are required when status is binds`.

**Rationale**: Three-valued applicability with ruled-out-with-reason (D13) and the quoted, dated register format (D22). An obligation under a ruled-out regime is a contradiction the file should not be able to express.

**Security Scan Note**: Asymmetric rules per status are intentional; `undetermined` and `no-longer-applies` are deliberately unconstrained beyond the required keys.

### Filename must equal the frontmatter id

**Decision**: `load_all` adds `filename X.md does not match id Y` when the stem differs from `meta.id`; the regime is still loaded under `meta.id`.

**Rationale**: `affects` lists in pending entries, `review_by` checks and human navigation all key on the id; a renamed file would silently split identity.

**Security Scan Note**: Regime ids are never used as path components by this module; the check is about identity, not path safety.

### Unknown statuses are loaded but not counted

**Decision**: A regime whose status is outside the four is kept in `load_all` with its raw status string and a `status: must be one of …` problem, but `counts` ignores it.

**Rationale**: Reporting it as a problem is loud; inventing a bucket for it would be a verdict. Counting only known states keeps the status line truthful.

**Security Scan Note**: Silent exclusion from counts is paired with an explicit problem row; not a lost record.

## Related Specs

- [SPEC-003: Pending: append-only pending.jsonl and resolutions.jsonl](./SPEC-003-pending-append-only-logs.md) — pending entries key on regime ids via `affects`
- [SPEC-004: Rescan: confirmed-answer snapshot, drift detection and regime-new/regime-gone entries](./SPEC-004-rescan-snapshot-drift.md) — reads `applies.triggered_by` and regime status
- [SPEC-005: Status: counts, profile age and pending totals, never a verdict](./SPEC-005-status-counts-never-verdict.md) — renders `counts` and per-regime problems
- [SPEC-006: Search: BM25 over compliance markdown](./SPEC-006-search-bm25-signature-index.md) — indexes `regimes/*.md` as kind `regime`
- [SPEC-016: check command: three-valued freshness, pending entries, date-passed and profile-stale](../integration/SPEC-016-check-command.md)
- [SPEC-021: Validators: profile validate, regimes validate, sources validate (exit 1 with problems, network-free)](../api/SPEC-021-validators.md)
- [SPEC-029: Frontmatter: YAML block read/write, atomic save, ISO date normalisation](../infra/SPEC-029-frontmatter-yaml-atomic-save-date-normalisation.md)
- [SPEC-031: Shipped references: method files, regime template, dimensions checklist and SPARQL template carry the method, never the law](../infra/SPEC-031-shipped-references-method-never-law.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan; certainty 91 |
