---
id: SPEC-029
title: "Frontmatter: YAML block read/write, atomic save, ISO date normalisation"
category: infra
tags: [infra, frontmatter, yaml, atomic-write]
status: implemented
certainty: 90
created: 2026-09-20
updated: 2026-09-20
related_code:
  - compliance_register/frontmatter.py
  - tests/test_frontmatter.py
  - compliance_register/profile.py
  - compliance_register/regimes.py
  - compliance_register/mirror/store.py
  - compliance_register/cli.py
  - tests/test_poisoned_files_do_not_brick.py
intentional_decisions:
  - "YAML dates are converted to ISO strings at load time, once"
  - "Only yaml.safe_load / yaml.safe_dump are used"
  - "save writes a hidden .tmp file in the target directory and renames over the target"
  - "A file whose closing fence is the last line without a trailing newline is accepted with an empty body"
  - "dump emits a blank line after the closing fence and loads strips exactly one leading newline"
behaviors:
  - behavior_id: BEH-246
    title: "loads parses a nested frontmatter block into a dict and body, and dump→loads round-trips both unchanged"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_frontmatter.py::test_loads_roundtrip
  - behavior_id: BEH-247
    title: "Text that does not start with a --- fence is returned as an empty dict and the unchanged body"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_frontmatter.py::test_loads_without_frontmatter
  - behavior_id: BEH-248
    title: "A block that opens with --- but never closes raises FrontmatterError"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_frontmatter.py::test_loads_rejects_unterminated
  - behavior_id: BEH-249
    title: "A block whose YAML is not a mapping (e.g. a list) raises FrontmatterError"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-250
    title: "A closing fence at end of file without a trailing newline is accepted and yields an empty body"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-251
    title: "save leaves the target file starting with the fence and no *.tmp file behind in the directory"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_frontmatter.py::test_save_is_atomic
  - behavior_id: BEH-252
    title: "dump preserves the insertion order of keys instead of sorting them"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_frontmatter.py::test_dump_keeps_key_order
  - behavior_id: BEH-253
    title: "Unquoted YAML dates and datetimes, including inside nested lists, load as ISO strings and the result is JSON-serialisable"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_frontmatter.py::test_loads_normalises_dates
  - behavior_id: BEH-254
    title: "A regime file with a malformed frontmatter block is reported as a problem by regimes.load_all rather than raising through the loader"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_regime_with_bad_frontmatter_is_reported_not_fatal
---

# Frontmatter: YAML block read/write, atomic save, ISO date normalisation

## What

`compliance_register/frontmatter.py` is the only module that reads or writes a YAML frontmatter block; every other module receives a `(dict, body)` pair.

- `loads(text)` returns `({}, text)` when the text does not start with `---\n`; otherwise it locates the closing `\n---\n` (or a closing `\n---` at end of file, giving an empty body), parses the block with `yaml.safe_load`, raises `FrontmatterError` if the block is unterminated or is not a mapping, strips exactly one leading newline from the body, and normalises every `date`/`datetime` value (recursively through dicts and lists) to its ISO string.
- `load(path)` reads UTF-8 and calls `loads`.
- `dump(meta, body)` emits `---\n<yaml>---\n\n<body>` with `safe_dump(sort_keys=False, allow_unicode=True)`.
- `save(path, meta, body)` creates parent directories, writes to a `.`-prefixed `.tmp` file created by `mkstemp` in the same directory with `newline='\n'`, then `os.replace`s it over the target, unlinking the temp file on any failure.

Consumers: `profile.load`, `regimes.load_all` (catches `FrontmatterError` and reports it as a per-regime problem), `mirror/store.write_page`, and `cli.init`/`profile diff`; an uncaught `FrontmatterError` is mapped by `cli.main` to `error:` and exit 1.

## Why

Profile, regime files and mirrored pages are markdown-with-frontmatter by D22 so they stay human-readable and git-diffable (principle 7). Hand-authored files are untrusted input (principle 10), so only `yaml.safe_*` is used and malformed blocks produce a typed error the caller can report instead of a traceback (principle 9). Date normalisation exists because PyYAML resolves an unquoted `2026-09-20` to a `datetime.date`, which crashed `status --json` and `rescan` on hand-written files (commit 933394e); normalising once at load means every downstream comparison and `json.dumps` sees strings. Atomic save via temp-file-plus-rename means a crash mid-write never leaves a truncated register file — the failure mode of a compliance tool must be 'it told me', not a half-written `profile.md`. Fixed `\n` line endings and UTF-8 keep diffs stable across platforms (plan A global constraint).

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-246 loads parses a nested frontmatter block into a dict and body, and dump→loads round-trips both unchanged | proposed | `tests/test_frontmatter.py::test_loads_roundtrip` |
| BEH-247 Text that does not start with a --- fence is returned as an empty dict and the unchanged body | proposed | `tests/test_frontmatter.py::test_loads_without_frontmatter` |
| BEH-248 A block that opens with --- but never closes raises FrontmatterError | proposed | `tests/test_frontmatter.py::test_loads_rejects_unterminated` |
| BEH-249 A block whose YAML is not a mapping (e.g. a list) raises FrontmatterError | proposed | — (test owed) |
| BEH-250 A closing fence at end of file without a trailing newline is accepted and yields an empty body | proposed | — (test owed) |
| BEH-251 save leaves the target file starting with the fence and no *.tmp file behind in the directory | proposed | `tests/test_frontmatter.py::test_save_is_atomic` |
| BEH-252 dump preserves the insertion order of keys instead of sorting them | proposed | `tests/test_frontmatter.py::test_dump_keeps_key_order` |
| BEH-253 Unquoted YAML dates and datetimes, including inside nested lists, load as ISO strings and the result is JSON-serialisable | proposed | `tests/test_frontmatter.py::test_loads_normalises_dates` |
| BEH-254 A regime file with a malformed frontmatter block is reported as a problem by regimes.load_all rather than raising through the loader | proposed | `tests/test_poisoned_files_do_not_brick.py::test_regime_with_bad_frontmatter_is_reported_not_fatal` |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### YAML dates are converted to ISO strings at load time, once

**Decision**: `loads` walks the parsed mapping and replaces every `datetime.date`/`datetime.datetime` with `.isoformat()`; no module downstream ever sees a date object.

**Rationale**: Hand-authored `confirmed_at: 2026-09-20` is legal YAML and resolves to a date; string comparison and JSON output are what the rest of the codebase does. Converting at the single read site is smaller and safer than teaching each consumer (commit 933394e).

**Security Scan Note**: Loss of type information is intended; not a bug. A reviewer expecting `datetime` objects from frontmatter should read `_dates_to_str`. This is intentional — see SPEC-029.

### Only yaml.safe_load / yaml.safe_dump are used

**Decision**: `frontmatter.py` never calls `yaml.load` or `yaml.dump`; the YAML error is wrapped into `FrontmatterError` so callers catch one type.

**Rationale**: Frontmatter blocks come from files in the target repo and from mirrored regulator pages — untrusted text (principle 10). `safe_load` cannot construct arbitrary Python objects.

**Security Scan Note**: No unsafe YAML deserialisation exists in this module; a grep over the whole package confirms no `yaml.load(` anywhere. This is intentional — see SPEC-029.

### save writes a hidden .tmp file in the target directory and renames over the target

**Decision**: `mkstemp(dir=path.parent, prefix='.', suffix='.tmp')` then `os.replace`; the temp file is unlinked in `finally` if the rename did not happen.

**Rationale**: Rename is atomic only on the same filesystem, so the temp file must live beside the target; `mkstemp` creates it 0600 with a unique name. Readers never observe a partially written profile or regime file (principle 9). The same pattern is repeated in `sources.save` and `store.save_manifest`.

**Security Scan Note**: 'Temp file in a writable directory' findings do not apply: the directory is the register's own, the file is created with O_EXCL by `mkstemp`, and the name is never predictable. The `.` prefix keeps a leftover from being indexed by `search` (which skips dot-files). This is intentional — see SPEC-029.

### A file whose closing fence is the last line without a trailing newline is accepted with an empty body

**Decision**: `loads` treats `---\nid: X\n---` (no final newline) as a terminated block with body `''` instead of raising.

**Rationale**: Editors and `init`-generated stubs may drop the trailing newline; refusing such a file would brick a valid profile over whitespace.

**Security Scan Note**: Not a parser laxity issue; the block boundary is still required to be a line consisting solely of `---`. This is intentional — see SPEC-029.

### dump emits a blank line after the closing fence and loads strips exactly one leading newline

**Decision**: Round-tripping `dump` → `loads` returns the identical body; a body that itself starts with a blank line loses one newline on load.

**Rationale**: Stable round-trips are what make `save` safe to call on a file that was just loaded (profile confirm, regime status change) without churning the diff.

**Security Scan Note**: Cosmetic; no data-loss concern beyond one leading blank line, and no consumer relies on a leading blank line. This is intentional — see SPEC-029.

## Related Specs

- [SPEC-028: Paths: project root discovery and write containment](./SPEC-028-paths-root-discovery-and-write-containment.md)
- [SPEC-030: Packaging: SKILL.md contract, plugin manifests, path launcher and version](./SPEC-030-packaging-skill-md-plugin-launcher-version.md)
- [SPEC-031: Shipped references carry the method, never the law](./SPEC-031-shipped-references-method-never-law.md)
- [SPEC-001: Profile: 15 dimensions, propose/confirm lifecycle, null blocks](../features/SPEC-001-profile-dimensions-propose-confirm.md)
- [SPEC-002: Regimes: one file per regime, frontmatter validation, obligation parsing and counts](../features/SPEC-002-regimes-one-file-per-regime.md)
- [SPEC-009: Mirror store: source directories, provenance frontmatter, per-source manifest](../integration/SPEC-009-mirror-store.md)
- [SPEC-017: CLI dispatch, exit-code contract and refusal boundary (main)](../api/SPEC-017-cli-dispatch-exit-codes.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Scan-generated from `frontmatter.py`, its tests, commit 933394e and design decision D22 |
