---
id: SPEC-024
title: 'render.printable: escape at the terminal sink'
category: api
tags: [api, render, escape-at-sink, principle-10, ADR-008]
status: implemented
certainty: 94
created: 2026-09-20
updated: 2026-09-20
related_code:
  - compliance_register/render.py
  - compliance_register/cli.py
  - compliance_register/status.py
  - tests/test_cli.py
intentional_decisions:
  - "render.py is a verbatim copy of docs-mirror's and must not be edited locally"
  - "Literal backslash sequences are not doubled, so \\x1b typed as six characters is indistinguishable from an escaped ESC"
  - "The escape set is wider than a URL refusal set on purpose (Cn, Cf, Zs-except-space all escaped)"
  - "No imports and no dependency on any other module"
behaviors:
  - behavior_id: BEH-207
    title: 'ESC (U+001B) in a printed regime body is rendered as the four characters \x1b and no raw ESC byte reaches stdout'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_search_output_escapes_terminal_controls
  - behavior_id: BEH-208
    title: 'U+202E in a printed body is rendered as \u202e'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_search_output_escapes_terminal_controls
  - behavior_id: BEH-209
    title: 'A pending summary containing ESC is printed with \x1b[2J and exits 0'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_pending_output_escapes_terminal_controls
  - behavior_id: BEH-210
    title: 'printable returns printable non-ASCII text (e.g. ''café'', ''日本語'') unchanged and the same object identity'
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-211
    title: 'printable maps \t, \n, \r to their mnemonics and codepoints above U+FFFF to \U followed by eight hex digits'
    state: proposed
    level: unit
    adapter: pytest
---

# render.printable: escape at the terminal sink

## What

`render.printable(text)` returns `text` unchanged when `str.isprintable()` is true and otherwise replaces each non-printable codepoint with an escape: `\t`, `\n`, `\r` for the three whitespace controls, `\xNN` up to U+00FF, `\uNNNN` up to U+FFFF and `\UNNNNNNNN` above. Printable non-ASCII (café, 日本語, العربية) passes through unchanged; ESC becomes `\x1b` and U+202E RIGHT-TO-LEFT OVERRIDE becomes `\u202e`.

The module has no imports and no knowledge of URLs, paths or sources. It is the single function the CLI and `status.render` call on every value that originated in a file (search snippets and paths, pending rows, check/fetch detail, status problem lines, validator output, exception messages). The file is a verbatim copy of docs-mirror's `render.py` and carries a header saying not to edit it here.

## Why

Principle 10 (from docs-mirror ADR-008): mirrored text is untrusted and a terminal is a state machine. An ESC in a regulator's page repaints it, a bidi override reverses what the operator reads. Escaping at the sink rather than refusing upstream is the only rule that holds regardless of which producer the text came from.

`isprintable` is used instead of `repr` because repr's quoting and doubled backslashes make a search result unreadable, and unreadable escaping is the kind that gets deleted. The Unicode category test is deliberately wider than any URL refusal set: over-escaping costs one `\xad` in a preview line, over-refusing costs a source.

Open question: there is no `tests/test_render.py`; the unit-level behaviours are covered only indirectly through the CLI tests. Is a direct unit test wanted here, or is docs-mirror's own suite considered the owner?

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-207 ESC (U+001B) in a printed regime body is rendered as the four characters \x1b and no raw ESC byte reaches stdout | proposed | `tests/test_cli.py::test_search_output_escapes_terminal_controls` |
| BEH-208 U+202E in a printed body is rendered as \u202e | proposed | `tests/test_cli.py::test_search_output_escapes_terminal_controls` |
| BEH-209 A pending summary containing ESC is printed with \x1b[2J and exits 0 | proposed | `tests/test_cli.py::test_pending_output_escapes_terminal_controls` |
| BEH-210 printable returns printable non-ASCII text (e.g. 'café', '日本語') unchanged and the same object identity | proposed | — (test owed) |
| BEH-211 printable maps \t, \n, \r to their mnemonics and codepoints above U+FFFF to \U followed by eight hex digits | proposed | — (test owed) |

## Intentional Design Decisions

### render.py is a verbatim copy of docs-mirror's and must not be edited locally

**Decision**: The module is copied, header-marked, and any change is expected to happen upstream and be re-copied.

**Rationale**: The sink guard is shared by design across the two tools so that one review covers both; a local fork would drift.

**Security Scan Note**: Duplicate-code findings against docs-mirror are expected; do not propose a shared dependency (principle 11: stdlib + PyYAML only).

### Literal backslash sequences are not doubled, so `\x1b` typed as six characters is indistinguishable from an escaped ESC

**Decision**: Output is for reading, not round-tripping; backslashes in the input pass through untouched.

**Rationale**: Resolving the ambiguity means becoming `repr`, whose readability cost is the reason the function exists. Nothing in either rendering can move the cursor.

**Security Scan Note**: An "escape ambiguity" finding is documented and accepted in the docstring.

### The escape set is wider than a URL refusal set on purpose (Cn, Cf, Zs-except-space all escaped)

**Decision**: Everything `isprintable()` rejects is escaped, including soft hyphen and unassigned codepoints.

**Rationale**: Escaping is cheap and refusing is expensive, so the two must not share a set; a codepoint newer than the running Python is escaped, which is the safe direction.

**Security Scan Note**: n/a

### No imports and no dependency on any other module

**Decision**: `render.py` imports nothing.

**Rationale**: A sink guard that depended on anything could be defeated by changing that thing.

**Security Scan Note**: n/a

## Related Specs

- [SPEC-017: CLI dispatch, exit-code contract and refusal boundary](./SPEC-017-cli-dispatch-exit-codes.md)
- [SPEC-019: status, pending, search: read-only reports](./SPEC-019-status-pending-search.md)
- [SPEC-005: Status: counts, profile age and pending totals, never a verdict](../features/SPEC-005-status-counts-never-verdict.md)
- [SPEC-006: Search: BM25 over compliance markdown with a signature-keyed derived index](../features/SPEC-006-search-bm25-signature-index.md)
- [SPEC-028: Paths: project root discovery and write containment](../infra/SPEC-028-paths-root-discovery-and-write-containment.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan by freya-spec-manager |
