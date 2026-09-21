---
id: SPEC-025
title: 'sources.json model: Source dataclass, defaults, atomic load/save, typed SourcesError'
category: api
tags: [api, sources, model, D17, D24, D28, principle-2, principle-9]
status: implemented
certainty: 92
created: 2026-09-20
updated: 2026-09-20
related_code:
  - compliance_register/sources.py
  - compliance_register/mirror/adapters/__init__.py
  - tests/test_sources.py
  - tests/test_poisoned_files_do_not_brick.py
intentional_decisions:
  - "Unknown keys in a source entry are silently dropped (notably `robots`)"
  - "licence.redistribute defaults to false"
  - "allowed_hosts defaults to the source URL's host and a bare string is promoted to a list"
  - "status defaults to proposed; nothing in the model can set confirmed"
behaviors:
  - behavior_id: BEH-212
    title: 'A source round-trips through load/save with last_version preserved and adapter eurlex kept'
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_roundtrip
  - behavior_id: BEH-213
    title: 'A `robots` key is dropped on load and the module exposes no ROBOTS constant'
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_no_robots_field_or_posture
  - behavior_id: BEH-214
    title: 'adapter defaults from tier: page-hash → pagehash'
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_default_adapter_from_tier
  - behavior_id: BEH-215
    title: 'allowed_hosts defaults to the URL''s hostname when absent'
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_allowed_hosts_defaults_to_url_host
  - behavior_id: BEH-216
    title: 'A bare-string allowed_hosts is wrapped into a one-element list'
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_allowed_hosts_string_is_wrapped_and_bad_shapes_refused
  - behavior_id: BEH-217
    title: 'get() raises KeyError for an unknown id'
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_sources.py::test_get_unknown
  - behavior_id: BEH-218
    title: 'load raises SourcesError on invalid JSON and on a top-level list'
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_poisoned_files_do_not_brick.py::test_corrupt_sources_json_is_a_typed_error_and_exit_1
  - behavior_id: BEH-219
    title: 'load returns an empty list when sources.json does not exist'
    state: proposed
    level: unit
    adapter: pytest
---

# sources.json model: Source dataclass, defaults, atomic load/save, typed SourcesError

## What

`sources.Source` is a dataclass with `id`, `jurisdiction`, `kind`, `url`, `covers`, `tier` (default `page-hash`), `adapter`, `config`, `change_signal`, `licence` (default `redistribute` false), `allowed_hosts`, `headers` (`user_agent` default), `delay_seconds` (10), `status` (`proposed`), `last_checked`/`last_status`/`last_version`/`next_version`/`last_fetched` and `evidence`.

`Source.from_dict` keeps only declared fields (an unknown key such as `robots` is dropped), fills `adapter` from tier via `{sitemap: sitemap, feed: feed, page-hash: pagehash}` (`api` gets none), wraps a bare-string `allowed_hosts` into a one-element list, and defaults an empty `allowed_hosts` to the URL's hostname.

`load(cdir)` returns `[]` when `sources.json` is absent, raises `SourcesError` on invalid JSON, on a top level that is not an object with a `sources` list, and on a malformed entry (`TypeError`/`ValueError`/`AttributeError` from the constructor). `save` writes `{schema: 1, sources: [...]}` through a temp file and `os.replace`. `get` raises `KeyError` for an unknown id. The constants `TIERS`, `KINDS`, `STATUSES`, `FRESHNESS` fix the vocabularies.

## Why

D17 and principle 2: no source address ships with the skill; every source is discovered by the agent, proposed with evidence, and confirmed by a human, hence `status` defaults to `proposed` and `evidence` is a list. D24: robots posture is never per-source, so a `robots` key is dropped rather than honoured.

Principle 9: a corrupt `sources.json` is a typed, named error (exit 1 from the CLI) that other commands (`status`, `pending`, `search`) do not depend on. Atomic save keeps the file readable if a fetch is interrupted, which matters because `sources.json` is committed history (principle 7).

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-212 A source round-trips through load/save with last_version preserved and adapter eurlex kept | proposed | `tests/test_sources.py::test_roundtrip` |
| BEH-213 A `robots` key is dropped on load and the module exposes no ROBOTS constant | proposed | `tests/test_sources.py::test_no_robots_field_or_posture` |
| BEH-214 adapter defaults from tier: page-hash → pagehash | proposed | `tests/test_sources.py::test_default_adapter_from_tier` |
| BEH-215 allowed_hosts defaults to the URL's hostname when absent | proposed | `tests/test_sources.py::test_allowed_hosts_defaults_to_url_host` |
| BEH-216 A bare-string allowed_hosts is wrapped into a one-element list | proposed | `tests/test_sources.py::test_allowed_hosts_string_is_wrapped_and_bad_shapes_refused` |
| BEH-217 get() raises KeyError for an unknown id | proposed | `tests/test_sources.py::test_get_unknown` |
| BEH-218 load raises SourcesError on invalid JSON and on a top-level list | proposed | `tests/test_poisoned_files_do_not_brick.py::test_corrupt_sources_json_is_a_typed_error_and_exit_1` |
| BEH-219 load returns an empty list when sources.json does not exist | proposed | — (test owed) |

## Intentional Design Decisions

### Unknown keys in a source entry are silently dropped (notably `robots`)

**Decision**: `from_dict` filters to declared dataclass fields; there is no `ROBOTS` constant and no per-source robots posture.

**Rationale**: D24 and principle 8: robots.txt is always honoured, without exception; a per-source override would be the bypass the constitution forbids. Dropping instead of erroring keeps an old file loadable.

**Security Scan Note**: A scanner should not report "robots: ignore is accepted"; the key never reaches the model.

### licence.redistribute defaults to false

**Decision**: A source without an explicit licence is treated as non-redistributable, so its mirror goes to `mirror/.private/` (gitignored).

**Rationale**: Principle 7 / D23: non-redistributable text must not enter git; the safe default is private until a human records the licence.

**Security Scan Note**: n/a

### allowed_hosts defaults to the source URL's host and a bare string is promoted to a list

**Decision**: An absent list becomes `[urlsplit(url).hostname]`; a string becomes `[string]`.

**Rationale**: The redirect boundary checks `hostname in allowed_hosts`; with a string that would be a substring test (commit 35691ce), so the shape is normalised at load and refused at validate for anything else.

**Security Scan Note**: This is the fix for a redirect-boundary weakening, not a lax coercion.

### status defaults to proposed; nothing in the model can set confirmed

**Decision**: Only a human editing `sources.json` changes `status` to `confirmed`; no code path writes it.

**Rationale**: Principle 3 / D7: code proposes, humans decide. `check` and `fetch` act only on confirmed sources unless one is named, and a named unconfirmed source is refused.

**Security Scan Note**: n/a

## Related Specs

- [SPEC-021: Validators: profile validate, regimes validate, sources validate](./SPEC-021-validators.md)
- [SPEC-026: sources.validate and refusals](./SPEC-026-sources-validate-refusals.md)
- [SPEC-007: HTTP client: judged redirects, budgets, retries, robots, politeness](../integration/SPEC-007-http-client.md)
- [SPEC-010: Adapter contract, registry and shared guards](../integration/SPEC-010-adapter-contract.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan by freya-spec-manager |
