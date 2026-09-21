---
id: SPEC-018
title: 'init: idempotent scaffold of knowledge-base/compliance/'
category: api
tags: [api, cli, init, D20, D23, principle-7]
status: implemented
certainty: 93
created: 2026-09-20
updated: 2026-09-20
related_code:
  - compliance_register/cli.py
  - compliance_register/profile.py
  - compliance_register/frontmatter.py
  - tests/test_cli.py
intentional_decisions:
  - "init never overwrites an existing profile.md, sources.json or .gitignore content"
  - "mirror/.private/ is gitignored by the scaffold itself"
behaviors:
  - behavior_id: BEH-175
    title: 'init creates profile.md, regimes/, mirror/.gitignore (.private/), sources.json with schema 1 and an empty list, and adds .search-index.json to .gitignore'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_init_scaffolds
  - behavior_id: BEH-176
    title: 'Running init twice exits 0 and leaves existing files unchanged'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_init_twice_is_safe
  - behavior_id: BEH-177
    title: 'After init, status --json reports the profile as present with zero binding regimes'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_status_json
  - behavior_id: BEH-178
    title: 'init does not append a duplicate .search-index.json line to an existing .gitignore'
    state: proposed
    level: component
    adapter: pytest
---

# init: idempotent scaffold of knowledge-base/compliance/

## What

`compliance-register init` creates `knowledge-base/compliance/` under the discovered project root with `regimes/` and `mirror/` directories, a `mirror/.gitignore` containing `.private/`, an empty 15-dimension `profile.md` (frontmatter from `profile.empty()` plus a notes body), and a `sources.json` of `{"schema": 1, "sources": []}`. It appends `.search-index.json` to `knowledge-base/compliance/.gitignore` if that line is absent.

Every file is created only when missing, so a second `init` changes nothing and exits 0. It prints `initialised knowledge-base/compliance` and returns 0. It never touches an existing profile, sources file or regime.

## Why

D20 and principle 7: code lives in the skill, data lives in the project, committed. The scaffold fixes the one layout every other command reads (D22, workflow.md §layout) so a fresh agent can run `status` immediately.

`.private/` is gitignored at the mirror level because non-redistributable text must not enter the project's history (D23, principle 7); `.search-index.json` is a derived cache and is gitignored at the compliance level. Idempotence matters because SKILL.md tells the agent to run `init` whenever the directory is missing.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-175 init creates profile.md, regimes/, mirror/.gitignore (.private/), sources.json with schema 1 and an empty list, and adds .search-index.json to .gitignore | proposed | `tests/test_cli.py::test_init_scaffolds` |
| BEH-176 Running init twice exits 0 and leaves existing files unchanged | proposed | `tests/test_cli.py::test_init_twice_is_safe` |
| BEH-177 After init, status --json reports the profile as present with zero binding regimes | proposed | `tests/test_cli.py::test_status_json` |
| BEH-178 init does not append a duplicate .search-index.json line to an existing .gitignore | proposed | — (test owed) |

## Intentional Design Decisions

### init never overwrites an existing profile.md, sources.json or .gitignore content

**Decision**: Each artifact is written only when its file does not exist; the top-level `.gitignore` is appended to, not replaced.

**Rationale**: The register is part of the project's history (principle 7). A re-run after a `profile` stage must not reset confirmed answers; a hand-maintained `.gitignore` must keep its lines.

**Security Scan Note**: Existing files are read and preserved by design; this is not a missing-overwrite-protection finding.

### mirror/.private/ is gitignored by the scaffold itself

**Decision**: `init` writes `mirror/.gitignore` with `.private/` before any fetch can happen.

**Rationale**: Principle 7 / D23: mirrored text whose `licence.redistribute` is false goes under `.private/` and must never be committed. Doing it in `init` means there is no window where a fetch precedes the ignore rule.

**Security Scan Note**: Intended data-handling control, not an accidental exclusion.

## Related Specs

- [SPEC-017: CLI dispatch, exit-code contract and refusal boundary](./SPEC-017-cli-dispatch-exit-codes.md)
- [SPEC-019: status, pending, search: read-only reports](./SPEC-019-status-pending-search.md)
- [SPEC-021: Validators: profile validate, regimes validate, sources validate](./SPEC-021-validators.md)
- [SPEC-001: Profile: 15 dimensions, propose/confirm lifecycle, null blocks](../features/SPEC-001-profile-dimensions-propose-confirm.md)
- [SPEC-028: Paths: project root discovery and write containment](../infra/SPEC-028-paths-root-discovery-and-write-containment.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan by freya-spec-manager |
