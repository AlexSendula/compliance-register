---
id: SPEC-028
title: "Paths: project root discovery and write containment"
category: infra
tags: [infra, paths, security, containment]
status: implemented
certainty: 92
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/paths.py
  - tests/test_paths.py
  - tests/conftest.py
  - compliance_register/cli.py
  - compliance_register/mirror/store.py
  - compliance_register/search.py
  - tests/test_cli.py
  - tests/test_store.py
intentional_decisions:
  - "A project is a directory with knowledge-base/, not a git repository"
  - "Containment is decided on resolved paths, symlinks followed"
  - "safe_component is a strict ASCII allowlist (1–128 chars, no leading dot)"
  - "Only cli.main turns NotAProject/UnsafePath into exit codes"
behaviors:
  - behavior_id: BEH-235
    title: "find_root returns the nearest ancestor that contains knowledge-base/ when started from a nested directory"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_paths.py::test_find_root_walks_up
  - behavior_id: BEH-236
    title: "find_root raises NotAProject when no ancestor of the start directory has knowledge-base/"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_paths.py::test_find_root_refuses_outside_project
  - behavior_id: BEH-237
    title: "compliance_dir(root) is exactly <root>/knowledge-base/compliance"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_paths.py::test_compliance_dir
  - behavior_id: BEH-238
    title: "contained resolves a relative child path under the base and returns the absolute target"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_paths.py::test_contained_accepts_child
  - behavior_id: BEH-239
    title: "contained raises UnsafePath when a relative target uses ../ to leave the base"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_paths.py::test_contained_refuses_escape
  - behavior_id: BEH-240
    title: "contained follows symlinks: a link inside the base that resolves outside it is refused, and the base itself is accepted"
    state: confirmed
    level: unit
    adapter: pytest
  - behavior_id: BEH-241
    title: "safe_component rejects ../x, a/b, trailing space, empty string, a leading dot, and internal whitespace"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_paths.py::test_safe_component_rejects
  - behavior_id: BEH-242
    title: "safe_component accepts plain ASCII names with dots, dashes and digits such as GDPR and eu-eurlex-32016R0679"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_paths.py::test_safe_component_accepts
  - behavior_id: BEH-243
    title: "safe_component rejects non-ASCII characters and names longer than 128 characters (128 accepted, 129 refused)"
    state: confirmed
    level: unit
    adapter: pytest
  - behavior_id: BEH-244
    title: "Any command run outside a project exits 2 and the stderr message names knowledge-base"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_cli.py::test_outside_project_exits_2
  - behavior_id: BEH-245
    title: "A mirror page relpath that escapes the source directory is refused with UnsafePath before anything is written"
    state: accepted
    level: unit
    adapter: pytest
    locator: tests/test_store.py::test_write_page_refuses_escape
---

# Paths: project root discovery and write containment

## What

`compliance_register/paths.py` is the only module allowed to decide a path. `find_root(start)` resolves the start directory (default cwd) and walks upward until it finds a directory containing `knowledge-base/` (constant `KB`); if none exists it raises `NotAProject`. `compliance_dir(root)` returns `<root>/knowledge-base/compliance` (constants `KB`, `SUB`). `contained(base, target)` resolves both paths (following symlinks), accepts the base itself or any descendant, and raises `UnsafePath` for anything else, including a symlink inside the base that points outside. `safe_component(name)` accepts exactly one path segment matching `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$` (ASCII only, no leading dot, no separators, no whitespace, 1–128 characters) and raises `UnsafePath` otherwise.

Callers: `cli.py` (every command starts from `find_root`), `mirror/store.py` (jurisdiction and source id through `safe_component`, page relpath through `contained`), and `search.py` (a hit whose indexed path escapes the compliance dir is dropped). `cli.main` maps `NotAProject` and `UnsafePath` to exit 2 with a `refused:` line on stderr.

## Why

The register is data in the target project (principle 7, D20, D23): the tool must locate that project by its `knowledge-base/` marker and never write anywhere else. File names reach the tool from three untrusted directions — a regulator's page (mirror relpaths, server-supplied CELEX ids), a regime id in frontmatter, and a command-line argument — so principle 10 (escape at the sink, docs-mirror ADR-008) requires that every path component pass through one allowlist and one containment check rather than per-caller string checks. Following symlinks in `contained` closes the case where a prefix comparison on the unresolved string would pass but the write would land outside. A single raise-to-exit-2 mapping in `cli.main` implements principle 9 (refuse loudly, never brick) and D29's exit code contract.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-235 find_root returns the nearest ancestor that contains knowledge-base/ when started from a nested directory | accepted | `tests/test_paths.py::test_find_root_walks_up` |
| BEH-236 find_root raises NotAProject when no ancestor of the start directory has knowledge-base/ | accepted | `tests/test_paths.py::test_find_root_refuses_outside_project` |
| BEH-237 compliance_dir(root) is exactly <root>/knowledge-base/compliance | accepted | `tests/test_paths.py::test_compliance_dir` |
| BEH-238 contained resolves a relative child path under the base and returns the absolute target | accepted | `tests/test_paths.py::test_contained_accepts_child` |
| BEH-239 contained raises UnsafePath when a relative target uses ../ to leave the base | accepted | `tests/test_paths.py::test_contained_refuses_escape` |
| BEH-240 contained follows symlinks: a link inside the base that resolves outside it is refused, and the base itself is accepted | confirmed | — (test owed) |
| BEH-241 safe_component rejects ../x, a/b, trailing space, empty string, a leading dot, and internal whitespace | accepted | `tests/test_paths.py::test_safe_component_rejects` |
| BEH-242 safe_component accepts plain ASCII names with dots, dashes and digits such as GDPR and eu-eurlex-32016R0679 | accepted | `tests/test_paths.py::test_safe_component_accepts` |
| BEH-243 safe_component rejects non-ASCII characters and names longer than 128 characters (128 accepted, 129 refused) | confirmed | — (test owed) |
| BEH-244 Any command run outside a project exits 2 and the stderr message names knowledge-base | accepted | `tests/test_cli.py::test_outside_project_exits_2` |
| BEH-245 A mirror page relpath that escapes the source directory is refused with UnsafePath before anything is written | accepted | `tests/test_store.py::test_write_page_refuses_escape` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### A project is a directory with knowledge-base/, not a git repository

**Decision**: `find_root` looks for a `knowledge-base/` directory, never `.git`; a working tree without `knowledge-base/` is refused with exit 2 even inside a git repo.

**Rationale**: Principle 7 and D23: every target project already has `knowledge-base/` and the register lives under it; git is how the data is versioned, not how the project is found. `init` does not create `knowledge-base/` either — its presence is the opt-in.

**Security Scan Note**: A scanner may flag 'writes outside the repository root' or 'no repo boundary check'. The boundary is `knowledge-base/compliance/`, enforced by `contained`; the git root is irrelevant by design. This is intentional — see SPEC-028.

### Containment is decided on resolved paths, symlinks followed

**Decision**: `contained` calls `.resolve()` on both base and target before comparing, so a symlink under `compliance/` that points outside is refused (`UnsafePath`), and an absolute target is accepted only if it resolves under the base.

**Rationale**: Principle 10: a string-prefix check on an unresolved path is the classic bypass; resolving first makes the check about where bytes land. Verified by probe: a `link -> ../outside` inside base is refused.

**Security Scan Note**: Path-traversal findings on `store.write_page`, `search` snippets or regime file names should be cross-referenced to `paths.contained`; there is no string-prefix comparison anywhere. This is intentional — see SPEC-028.

### safe_component is a strict ASCII allowlist (1–128 chars, no leading dot)

**Decision**: Names with non-ASCII letters (e.g. `Ü`), whitespace, `/`, a leading `.`, or longer than 128 characters are rejected with `UnsafePath` — including otherwise legitimate-looking jurisdiction or regime names.

**Rationale**: Regime ids (`<ID>`, uppercase short abbreviation) and source ids (`<jurisdiction>-<short-name>`, lowercase, dashes) are ASCII by the conventions in `references/regime-template.md` and `method-discover-sources.md`; server-supplied strings (CELEX ids, jurisdiction codes) become directory names, so a small allowlist is safer than a denylist of separators. Leading-dot rejection keeps a source from creating hidden files or colliding with `.private/`.

**Security Scan Note**: Not a Unicode-handling bug and not an injection gap: rejection is the intended outcome; the CLI reports it as `refused:` with exit 2. This is intentional — see SPEC-028.

### Only cli.main turns NotAProject/UnsafePath into exit codes

**Decision**: `paths` raises typed exceptions and never prints or exits; `cli.main` catches `NotAProject` → exit 2 (message names `knowledge-base/`) and `UnsafePath` → exit 2 (`refused:`), both after passing the message through `render.printable`.

**Rationale**: D29 exit-code contract and principle 9: one place decides what a refusal looks like so library callers (tests, other modules) get exceptions and the terminal gets a consistent line. `search.py` deliberately catches `UnsafePath` locally to drop one poisoned hit instead of aborting the search.

**Security Scan Note**: Exception messages contain the offending path; they go through `printable` before stderr, so terminal-escape injection via a file name is neutralised at the sink. This is intentional — see SPEC-028.

## Related Specs

- [SPEC-029: Frontmatter: YAML block read/write, atomic save, ISO date normalisation](./SPEC-029-frontmatter-yaml-atomic-save-date-normalisation.md)
- [SPEC-030: Packaging: SKILL.md contract, plugin manifests, path launcher and version](./SPEC-030-packaging-skill-md-plugin-launcher-version.md)
- [SPEC-031: Shipped references carry the method, never the law](./SPEC-031-shipped-references-method-never-law.md)
- [SPEC-006: Search: BM25 over compliance markdown with a signature-keyed derived index](../features/SPEC-006-search-bm25-signature-index.md)
- [SPEC-009: Mirror store: source directories, provenance frontmatter, per-source manifest](../integration/SPEC-009-mirror-store.md)
- [SPEC-017: CLI dispatch, exit-code contract and refusal boundary (main)](../api/SPEC-017-cli-dispatch-exit-codes.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Scan-generated from `paths.py`, its tests and design decisions D20, D23, D29 |
| 2026-09-21 | Behaviours promoted by Alex: tested → accepted, untested → confirmed (test owed) | First behaviour review after the freya wrap-up |
