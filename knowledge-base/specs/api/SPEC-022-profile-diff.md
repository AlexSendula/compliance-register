---
id: SPEC-022
title: 'profile diff --against <file or git ref> with --end-of-options'
category: api
tags: [api, cli, profile, git, D18, argument-injection]
status: implemented
certainty: 92
created: 2026-09-20
updated: 2026-09-21
related_code:
  - compliance_register/cli.py
  - compliance_register/profile.py
  - compliance_register/frontmatter.py
  - tests/test_cli.py
intentional_decisions:
  - "The git ref is always placed after --end-of-options"
  - "A file path wins over a git ref of the same spelling"
  - "git's stderr passes through render.printable like every other sink"
behaviors:
  - behavior_id: BEH-195
    title: 'diff --against <older profile file> prints exactly the slugs whose value changed (e.g. ''sector'') and exits 0'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_profile_diff_against_file
  - behavior_id: BEH-196
    title: 'A ref such as --output=/tmp/x is passed after --end-of-options and never as a git option; git failure relays stderr and exits 1'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_cli.py::test_profile_diff_ref_is_never_a_git_option
  - behavior_id: BEH-197
    title: 'profile.diff ignores keys outside DIMENSIONS and reports only known slugs'
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-198
    title: 'diff without a current profile.md prints ''no profile.md'' to stderr and exits 1'
    state: proposed
    level: component
    adapter: pytest
---

# profile diff --against <file or git ref> with --end-of-options

## What

`profile diff --against REF` prints one dimension slug per line for each of the 15 dimensions whose `answers.<slug>.value` differs between the current `profile.md` and an older one, and exits 0.

REF is tried as a file path first; if no such file exists it is treated as a git ref and the old profile is read with `git show --end-of-options <ref>:knowledge-base/compliance/profile.md` (list argv, no shell, path relative to the discovered root). A missing current profile prints `no profile.md` and exits 1. A git failure prints git's stderr (or `cannot read <ref>`) and exits 1. Output slugs come from `profile.DIMENSIONS` only; unknown keys in either profile are ignored.

## Why

D18 (incremental): `rescan` and the human reviewer want to know which dimensions moved, not the whole diff. Comparing against a git ref lets a reviewer ask "what changed since the last confirmed profile" without copying files.

`--end-of-options` exists because the ref is operator-typed and a value like `--output=/tmp/x` would otherwise be parsed by git as an option (commit 8ee0520), an argument-injection class the tool must not have.

Open question: should git's stderr be passed through `render.printable` for consistency, given a git hook or a pathological ref name could contain control characters? Currently classified as operator-supplied.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-195 diff --against <older profile file> prints exactly the slugs whose value changed (e.g. 'sector') and exits 0 | proposed | `tests/test_cli.py::test_profile_diff_against_file` |
| BEH-196 A ref such as --output=/tmp/x is passed after --end-of-options and never as a git option; git failure relays stderr and exits 1 | proposed | `tests/test_cli.py::test_profile_diff_ref_is_never_a_git_option` |
| BEH-197 profile.diff ignores keys outside DIMENSIONS and reports only known slugs | proposed | — (test owed) |
| BEH-198 diff without a current profile.md prints 'no profile.md' to stderr and exits 1 | proposed | — (test owed) |

## Intentional Design Decisions

### The git ref is always placed after --end-of-options

**Decision**: `git show --end-of-options <ref>:<path>` is used so no ref value can be read by git as an option.

**Rationale**: REF comes from the command line; without the sentinel `--against=--output=/tmp/x` would make git write a file. The test pins the argv shape.

**Security Scan Note**: This is the mitigation for argument injection into git; do not report "user input passed to git" without noting the sentinel and list-form `subprocess.run`.

### A file path wins over a git ref of the same spelling

**Decision**: `Path(ref).is_file()` is checked first; only then is REF treated as a git ref.

**Rationale**: Simplest interface: one flag for both. A file named like a ref (e.g. `HEAD`) in the cwd is an unlikely collision and the file interpretation is the more explicit one.

**Security Scan Note**: The file is read with `frontmatter.load`, which has its own size/shape guards; no write occurs.

### git's stderr passes through render.printable like every other sink

**Decision**: When `git show` fails, its stderr (stripped, or `cannot read <ref>` if empty) is printed through `render.printable` and the command exits 1.

**Rationale**: Principle 10 — everything printed to a terminal is escaped at the sink. git's message echoes the operator-typed ref, which is low-risk, but the rule has no exceptions and the cost is one call.

**Security Scan Note**: `test_profile_diff_ref_is_never_a_git_option` injects an ESC sequence into the fake stderr and asserts it does not reach the terminal.

## Related Specs

- [SPEC-017: CLI dispatch, exit-code contract and refusal boundary](./SPEC-017-cli-dispatch-exit-codes.md)
- [SPEC-021: Validators: profile validate, regimes validate, sources validate](./SPEC-021-validators.md)
- [SPEC-001: Profile: 15 dimensions, propose/confirm lifecycle, null blocks](../features/SPEC-001-profile-dimensions-propose-confirm.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan by freya-spec-manager |
| 2026-09-21 | git's stderr is now escaped through `render.printable`; open question closed | G3 contradiction check, principle 10 |
