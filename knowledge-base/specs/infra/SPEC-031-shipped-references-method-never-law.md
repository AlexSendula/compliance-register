---
id: SPEC-031
title: "Shipped references: method files, regime template, dimensions checklist and SPARQL template carry the method, never the law"
category: infra
tags: [infra, references, method, template, principle-2]
status: implemented
certainty: 85
created: 2026-09-20
updated: 2026-09-20
related_code:
  - references/dimensions-checklist.md
  - references/regime-template.md
  - references/method-profile.md
  - references/method-discover-sources.md
  - references/method-discover-regimes.md
  - references/method-register.md
  - references/eurlex-resolve.sparql
  - SKILL.md
  - README.md
  - tests/test_skill_md.py
  - compliance_register/profile.py
  - compliance_register/sources.py
  - compliance_register/mirror/adapters/eurlex.py
  - tests/test_adapter_eurlex.py
intentional_decisions:
  - "'Found in' provenance lines are the one place law citations may appear in shipped files"
  - "The regime template is placeholders, not a worked example"
  - "The SPARQL template ships with ontology namespace URIs and is not covered by the no-URL test"
  - "Method files forbid the agent from setting confirmed status and from using repo name, README or marketing copy as evidence"
  - "Profile changes route through rescan, not profile diff --against a git ref"
behaviors:
  - behavior_id: BEH-268
    title: "regime-template.md ships id: EXAMPLE, angle-bracket placeholders, EXAMPLE-001, the Obligations section and a Rules list, and contains no CELEX, ISO date or 'Art. N' citation"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_regime_template_ships_placeholders_not_law
  - behavior_id: BEH-269
    title: "method-discover-sources.md names every agent-written sources.Source field, every KINDS/TIERS/STATUSES value, every adapter config key, and says robots.txt is always honoured"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_method_discover_sources_names_every_source_field
  - behavior_id: BEH-270
    title: "method-profile.md routes profile changes through rescan, never '--against HEAD~1', and bars repo name as evidence for any answer while allowing locale indicia"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_method_profile_makes_rescan_the_baseline_and_bars_repo_name_as_evidence
  - behavior_id: BEH-271
    title: "method-discover-regimes.md mentions rescan and never 'profile diff' for the re-run loop"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_skill_md_documents_pending_kinds_severities_and_the_api_endpoint_rule
  - behavior_id: BEH-272
    title: "No line of SKILL.md, README.md or any references/*.md contains a CELEX number, ISO date, 'Art. N' citation or http(s) URL, except dimensions-checklist lines carrying '**Found in**'"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_shipped_docs_carry_no_law_fact_or_source_address
  - behavior_id: BEH-273
    title: "eurlex-resolve.sparql contains a {{VALUES}} placeholder that the eurlex adapter replaces with quoted CELEX strings, and the file names no instrument CELEX"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-274
    title: "The Slugs section of dimensions-checklist.md lists the fifteen slugs in the same order as profile.DIMENSIONS"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-275
    title: "Every dimension in dimensions-checklist.md carries the five fixed lines Ask, Decides, Code may propose, Trap and Found in"
    state: proposed
    level: unit
    adapter: pytest
---

# Shipped references: method files, regime template, dimensions checklist and SPARQL template carry the method, never the law

## What

`references/` holds the agent-driven method for stages 1–3 plus two machine-read files.

- `dimensions-checklist.md` lists the fifteen profile slugs in the order `profile.DIMENSIONS` uses and, per dimension, five fixed lines (Ask, Decides, Code may propose, Trap, Found in).
- `regime-template.md` shows the regime file shape with `id: EXAMPLE`, angle-bracket placeholders for every value (`<verbatim scope clause>`, `<Art. N(M)>`, `<YYYY-MM-DD>`, `<jurisdiction>-<short-name>`), one placeholder obligation `EXAMPLE-001`, the `## Obligations` section and a `Rules:` list.
- The four `method-*.md` files describe, per stage, what the agent does, what evidence counts, what it may never assert, and which CLI command to run before committing.
- `eurlex-resolve.sparql` is a CELLAR query template with a `{{VALUES}}` placeholder that `mirror/adapters/eurlex.py` fills with quoted CELEX ids at run time; it names only ontology namespace prefixes.

A test scans every line of SKILL.md, README.md and `references/*.md` and fails on any CELEX number, ISO date, `Art. N` citation or `http(s)://` URL, with the single exemption of `**Found in**` lines in the checklist. Further tests pin the template's placeholders, tie `method-discover-sources.md` to every agent-written `sources.Source` field and every `KINDS`/`TIERS`/`STATUSES` value, and require `method-profile.md` and `method-discover-regimes.md` to route profile changes through `rescan` rather than `profile diff --against HEAD~1`.

## Why

Principle 2 and D4/D5/D17: the skill ships questions and a method, never a rule, threshold, date, instrument or source address, because anything hardcoded is wrong on arrival and differs per jurisdiction. The regime template was rewritten to placeholders after the shipped example carried a real scope clause, article citation and version id that agents copied verbatim and that then went stale (commit e0b28a4). The checklist's `Found in` lines are provenance — they say which scope articles caused a question to exist, never what the answer is (D5) — which is why they are the one carve-out in the no-law-fact test (commit 4c139a8). Method files are tied to code constants so the document an agent follows cannot name fewer fields or kinds than `sources.py` validates (commit bb06b9d). The SPARQL template is protocol, not a source (D28): the endpoint and ontology are how CELLAR is spoken to; per-instrument CELEX ids arrive from `sources.json` at run time.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-268 regime-template.md ships id: EXAMPLE, angle-bracket placeholders, EXAMPLE-001, the Obligations section and a Rules list, and contains no CELEX, ISO date or 'Art. N' citation | proposed | `tests/test_skill_md.py::test_regime_template_ships_placeholders_not_law` |
| BEH-269 method-discover-sources.md names every agent-written sources.Source field, every KINDS/TIERS/STATUSES value, every adapter config key, and says robots.txt is always honoured | proposed | `tests/test_skill_md.py::test_method_discover_sources_names_every_source_field` |
| BEH-270 method-profile.md routes profile changes through rescan, never '--against HEAD~1', and bars repo name as evidence for any answer while allowing locale indicia | proposed | `tests/test_skill_md.py::test_method_profile_makes_rescan_the_baseline_and_bars_repo_name_as_evidence` |
| BEH-271 method-discover-regimes.md mentions rescan and never 'profile diff' for the re-run loop | proposed | `tests/test_skill_md.py::test_skill_md_documents_pending_kinds_severities_and_the_api_endpoint_rule` |
| BEH-272 No line of SKILL.md, README.md or any references/*.md contains a CELEX number, ISO date, 'Art. N' citation or http(s) URL, except dimensions-checklist lines carrying '**Found in**' | proposed | `tests/test_skill_md.py::test_shipped_docs_carry_no_law_fact_or_source_address` |
| BEH-273 eurlex-resolve.sparql contains a {{VALUES}} placeholder that the eurlex adapter replaces with quoted CELEX strings, and the file names no instrument CELEX | proposed | — (test owed) |
| BEH-274 The Slugs section of dimensions-checklist.md lists the fifteen slugs in the same order as profile.DIMENSIONS | proposed | — (test owed) |
| BEH-275 Every dimension in dimensions-checklist.md carries the five fixed lines Ask, Decides, Code may propose, Trap and Found in | proposed | — (test owed) |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### 'Found in' provenance lines are the one place law citations may appear in shipped files

**Decision**: `test_shipped_docs_carry_no_law_fact_or_source_address` skips only lines of `dimensions-checklist.md` containing `**Found in**`; those lines name scope articles (e.g. a GDPR article) and practice sources.

**Rationale**: D5: the checklist is the one fixed artifact and must show where each question came from so a new jurisdiction can add to or challenge it; a citation of where a question originates is not an applicability rule, threshold or date (principle 2).

**Security Scan Note**: A 'hardcoded regulatory reference' or 'legal text in repo' finding on those lines is expected and intentional; anywhere else in a shipped .md it would be a real violation and the test would fail. This is intentional — see SPEC-031.

### The regime template is placeholders, not a worked example

**Decision**: `regime-template.md` uses `id: EXAMPLE`, `<...>` placeholders for every quote, citation, version and date, and `EXAMPLE-001` as the obligation id; no real instrument is shown.

**Rationale**: An agent copies a worked example and its quote, version id and date go stale silently (commit e0b28a4); placeholders force every value to come from the source read that day (principle 3).

**Security Scan Note**: Angle-bracket tokens such as `<Art. N(M)>` are deliberate and excluded from the article-citation regex by the `N` letter; the template is not malformed YAML by accident. This is intentional — see SPEC-031.

### The SPARQL template ships with ontology namespace URIs and is not covered by the no-URL test

**Decision**: `eurlex-resolve.sparql` contains `PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>` and the XSD namespace; the shipped-docs scan covers only `.md` files.

**Rationale**: D28: an api adapter carries the endpoint and protocol of the API it speaks; an RDF namespace is part of the query language, not a source address. Per-instrument CELEX numbers are substituted from `sources.json` at run time.

**Security Scan Note**: Query injection via `{{VALUES}}` is bounded upstream: `eurlex.py` shape-checks every CELEX against `\d{5}[A-Z]{1,2}\d{4}` before it reaches the substitution, and the query is sent over https only (`test_sparql_endpoint_is_https`). This is intentional — see SPEC-031.

### Method files forbid the agent from setting confirmed status and from using repo name, README or marketing copy as evidence

**Decision**: `method-profile.md` states that `status: confirmed`, `confirmed_by` and `confirmed_at` are written only after the human answers, that `unknown` stays `value: null` (and `profile validate` will report it), and that repository name/README/marketing copy are never evidence for any answer; locale files are indicia to surface under question 2 only.

**Rationale**: Principle 3 and D7 (code proposes, humans decide), D9 (language ≠ jurisdiction). A `null` that blocks is preferred to an invented value that passes validation.

**Security Scan Note**: Not enforceable by code beyond `profile validate`; it is a documented instruction to the agent, which is why it is tested as text. This is intentional — see SPEC-031.

### Profile changes route through rescan, not profile diff --against a git ref

**Decision**: `method-profile.md` and `method-discover-regimes.md` must not mention `--against HEAD~1`/`profile diff` for the change loop; the snapshot the last `rescan` wrote is the one baseline (D18).

**Rationale**: A git-ref diff depends on commit granularity and can miss or double-count; the snapshot is exactly the confirmed answers at the last rescan, and `rescan` writes the pending entries a human resolves (D19).

**Security Scan Note**: `profile diff --against <ref>` still exists as a CLI convenience; it is the method that no longer relies on it. This is intentional — see SPEC-031.

## Related Specs

- [SPEC-028: Paths: project root discovery and write containment](./SPEC-028-paths-root-discovery-and-write-containment.md)
- [SPEC-029: Frontmatter: YAML block read/write, atomic save, ISO date normalisation](./SPEC-029-frontmatter-yaml-atomic-save-date-normalisation.md)
- [SPEC-030: Packaging: SKILL.md contract, plugin manifests, path launcher and version](./SPEC-030-packaging-skill-md-plugin-launcher-version.md)
- [SPEC-001: Profile: 15 dimensions, propose/confirm lifecycle, null blocks](../features/SPEC-001-profile-dimensions-propose-confirm.md)
- [SPEC-002: Regimes: one file per regime, frontmatter validation, obligation parsing and counts](../features/SPEC-002-regimes-one-file-per-regime.md)
- [SPEC-014: EUR-Lex adapter: SPARQL resolve, consolidated CELEX signal, guards, per-article chunking](../integration/SPEC-014-eurlex-adapter.md)
- [SPEC-025: sources.json model: Source dataclass, defaults, atomic load/save, typed SourcesError](../api/SPEC-025-sources-model.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Scan-generated from `references/`, `tests/test_skill_md.py`, commits e0b28a4, 4c139a8, bb06b9d and design decisions D4, D5, D17, D18, D19, D28 |
