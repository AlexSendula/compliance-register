---
id: SPEC-030
title: "Packaging: SKILL.md contract, plugin manifests, path launcher and version"
category: infra
tags: [infra, packaging, skill-md, plugin, launcher, version]
status: implemented
certainty: 88
created: 2026-09-20
updated: 2026-09-20
related_code:
  - SKILL.md
  - README.md
  - .claude-plugin/plugin.json
  - .claude-plugin/marketplace.json
  - pyproject.toml
  - requirements-dev.txt
  - bin/compliance-register
  - compliance_register/__init__.py
  - compliance_register/cli.py
  - compliance_register/mirror/http.py
  - tests/test_skill_md.py
  - tests/test_launcher.py
  - tests/test_http.py
intentional_decisions:
  - "No install step: the launcher puts its own repo on sys.path after resolving symlinks"
  - "Python < 3.12 and missing prerequisites exit 2 with a named cause before any package import"
  - "pyproject.toml is a dev convenience, not the distribution mechanism"
  - "The version string is written by hand in four places"
  - "SKILL.md is bound to the code by tests that walk the real parser and constants"
behaviors:
  - behavior_id: BEH-255
    title: "SKILL.md frontmatter has name equal to the repo directory 'compliance-register' in kebab-case ≤64 chars, a 1–1024 char description containing 'TRIGGER when', license MIT, and the file is under 500 lines"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_skill_md_frontmatter_matches_spec
  - behavior_id: BEH-256
    title: "SKILL.md never contains the verdict phrases 'you are compliant' or 'is compliant'"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_skill_md_never_says_compliant_as_a_verdict
  - behavior_id: BEH-257
    title: "plugin.json name is 'compliance-register' with skills ['.'], and marketplace.json's single plugin has the same name and source '.'"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_plugin_and_marketplace_agree
  - behavior_id: BEH-258
    title: "Every references/*.md path mentioned in SKILL.md exists on disk"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_every_reference_linked_from_skill_md_exists
  - behavior_id: BEH-259
    title: "The SKILL.md Commands section names every subcommand reachable from cli.build_parser, states that stage names are not CLI commands, and gives the check/fetch/rescan exit-code rules"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_skill_md_commands_table_covers_the_whole_cli
  - behavior_id: BEH-260
    title: "README lists every CLI command as 'compliance-register <name>' and names .last-check, profile.snapshot.json, mirror/.private/, .search-index.json and MANIFEST.json"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_readme_matches_the_cli_and_lists_engine_files
  - behavior_id: BEH-261
    title: "The SKILL.md Pending section names every pending.KINDS and pending.SEVERITIES value and the Mirror section states that api adapters carry only their endpoint"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_skill_md_documents_pending_kinds_severities_and_the_api_endpoint_rule
  - behavior_id: BEH-262
    title: "The SKILL.md Mirror section states the EUR-Lex v1 narrowings (never-consolidated acts cited by URL, language not pre-checked, G1/G2) and no eurlex-language.sparql ships"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_skill_md.py::test_skill_md_states_eurlex_v1_narrowings
  - behavior_id: BEH-263
    title: "Running the launcher with --version exits 0 and prints 'compliance-register <version>'"
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_launcher.py::test_launcher_prints_version
  - behavior_id: BEH-265
    title: "The default HTTP User-Agent string embeds __version__ and the contact address"
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_http.py::test_user_agent_strings
  - behavior_id: BEH-266
    title: "The version in __init__.py, pyproject.toml, plugin.json and SKILL.md metadata are identical"
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-267
    title: "Running the launcher under Python older than 3.12 exits 2 with a message naming the found version, before importing the package"
    state: proposed
    level: component
    adapter: pytest
---

# Packaging: SKILL.md contract, plugin manifests, path launcher and version

## What

The repository is one skill: the root `SKILL.md` frontmatter declares `name: compliance-register` (equal to the repo directory name, kebab-case, ≤64 chars), a `description` of 1–1024 characters containing `TRIGGER when`, `license: MIT`, a `compatibility` line naming Python 3.12+ and PyYAML, and `metadata.author`/`metadata.version`; the whole file stays under 500 lines. `.claude-plugin/plugin.json` declares the same name with `skills: ["."]`, and `.claude-plugin/marketplace.json` lists that one plugin with `source: "."`. `pyproject.toml` carries the same name/version, `requires-python >=3.12`, the single dependency `PyYAML`, a console-script entry point, and `[tool.pytest.ini_options]` with `testpaths=["tests"]` and `pythonpath=["."]`.

`bin/compliance-register` is the supported entry point: it exits 2 before any import if Python is older than 3.12, resolves its own real path (symlinks followed), inserts the repo directory at the front of `sys.path`, runs `preflight.check_prerequisites()` and exits 2 listing any missing prerequisite, then calls `cli.main`. `compliance_register.__version__` is the single Python source of the version string: `--version` prints `compliance-register <version>` and the default HTTP User-Agent embeds it.

Tests in `tests/test_skill_md.py` bind SKILL.md and README to the code: the Commands table must name every argparse subcommand found by walking `build_parser()`, the Pending section every `pending.KINDS` and `SEVERITIES`, and the Mirror section the EUR-Lex v1 narrowings.

## Why

Plan A's architecture is 'one repo = one skill, invoked by path with no install step', so the skill works identically from a git clone, `npx skills add` symlink, or a Claude plugin cache (D25 for the name; principle 11 for the footprint). The launcher does the Python-version and dependency checks itself because an `ImportError` traceback is not an actionable message for an agent, while 'PyYAML is not installed. Install it with …' is (principle 9). SKILL.md is the agent's only entry point, so tests that walk the real parser and the real constants stop the document from silently drifting from the CLI — commit 2162bb0 records that the table had already missed subcommands once. The frontmatter constraints mirror the Agent Skills spec limits so the skill is discoverable by any compliant installer. The 'never says compliant' test on SKILL.md is principle 1 (router, not oracle) applied to the document an agent reads first.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-255 SKILL.md frontmatter has name equal to the repo directory 'compliance-register' in kebab-case ≤64 chars, a 1–1024 char description containing 'TRIGGER when', license MIT, and the file is under 500 lines | proposed | `tests/test_skill_md.py::test_skill_md_frontmatter_matches_spec` |
| BEH-256 SKILL.md never contains the verdict phrases 'you are compliant' or 'is compliant' | proposed | `tests/test_skill_md.py::test_skill_md_never_says_compliant_as_a_verdict` |
| BEH-257 plugin.json name is 'compliance-register' with skills ['.'], and marketplace.json's single plugin has the same name and source '.' | proposed | `tests/test_skill_md.py::test_plugin_and_marketplace_agree` |
| BEH-258 Every references/*.md path mentioned in SKILL.md exists on disk | proposed | `tests/test_skill_md.py::test_every_reference_linked_from_skill_md_exists` |
| BEH-259 The SKILL.md Commands section names every subcommand reachable from cli.build_parser, states that stage names are not CLI commands, and gives the check/fetch/rescan exit-code rules | proposed | `tests/test_skill_md.py::test_skill_md_commands_table_covers_the_whole_cli` |
| BEH-260 README lists every CLI command as 'compliance-register <name>' and names .last-check, profile.snapshot.json, mirror/.private/, .search-index.json and MANIFEST.json | proposed | `tests/test_skill_md.py::test_readme_matches_the_cli_and_lists_engine_files` |
| BEH-261 The SKILL.md Pending section names every pending.KINDS and pending.SEVERITIES value and the Mirror section states that api adapters carry only their endpoint | proposed | `tests/test_skill_md.py::test_skill_md_documents_pending_kinds_severities_and_the_api_endpoint_rule` |
| BEH-262 The SKILL.md Mirror section states the EUR-Lex v1 narrowings (never-consolidated acts cited by URL, language not pre-checked, G1/G2) and no eurlex-language.sparql ships | proposed | `tests/test_skill_md.py::test_skill_md_states_eurlex_v1_narrowings` |
| BEH-263 Running the launcher with --version exits 0 and prints 'compliance-register <version>' | proposed | `tests/test_launcher.py::test_launcher_prints_version` |
| BEH-265 The default HTTP User-Agent string embeds __version__ and the contact address | proposed | `tests/test_http.py::test_user_agent_strings` |
| BEH-266 The version in __init__.py, pyproject.toml, plugin.json and SKILL.md metadata are identical | proposed | — (test owed) |
| BEH-267 Running the launcher under Python older than 3.12 exits 2 with a message naming the found version, before importing the package | proposed | — (test owed) |

Declarative decisions that are *not* executable are recorded under **Intentional
Design Decisions** below, not here.

## Intentional Design Decisions

### No install step: the launcher puts its own repo on sys.path after resolving symlinks

**Decision**: `bin/compliance-register` computes `os.path.realpath(__file__)`, inserts its parent's parent at `sys.path[0]`, and imports the package from there. The `[project.scripts]` entry point in pyproject.toml exists but is not the documented invocation.

**Rationale**: Skills installers symlink the skill directory into `~/.agents/skills/<name>`; without `realpath` the package would be looked for next to the symlink. Invocation by path keeps the skill droppable into any project with no `pip install` (plan A global constraints, principle 11).

**Security Scan Note**: The inserted path is derived from the launcher's own location, not from an argument or environment variable, so this is not a user-controlled sys.path injection. This is intentional — see SPEC-030.

### Python < 3.12 and missing prerequisites exit 2 with a named cause before any package import

**Decision**: The launcher checks `sys.version_info` first, then runs `preflight.check_prerequisites()` (PyYAML present, non-empty CA trust store) and prints each problem as a bullet with the install command, exit 2.

**Rationale**: D29 reserves exit 2 for 'refused'; SKILL.md tells the agent to relay the message and not work around it. The trust-store check exists because a python.org macOS Python with zero CA certificates made every https fetch read 'unreachable' (brainstorm §8.5).

**Security Scan Note**: The launcher never downloads or installs anything; it only names what the human should install. This is intentional — see SPEC-030.

### pyproject.toml is a dev convenience, not the distribution mechanism

**Decision**: `pythonpath = ["."]` under pytest options makes bare `pytest` resolve the package from any cwd (commit 6233e6e); no wheel is published and README installs via `npx skills add` or the plugin marketplace.

**Rationale**: The plugin/skills ecosystem distributes the directory, not a package; a wheel would create a second, divergent way to run the tool.

**Security Scan Note**: A 'package declares an entry point that is never exercised' finding is expected and harmless. This is intentional — see SPEC-030.

### The version string is written by hand in four places

**Decision**: `compliance_register/__init__.py`, `pyproject.toml`, `.claude-plugin/plugin.json` and `SKILL.md` `metadata.version` each carry `0.1.0`; `__version__` is the only one code reads (`--version`, User-Agent).

**Rationale**: Each consumer (Python, pip, plugin loader, skills spec) reads a different file format, and a build step to sync them would add tooling the skill otherwise does not need.

**Security Scan Note**: Not a security issue; noted because a drift between the four would be a release bug that no current test catches. This is intentional — see SPEC-030.

### SKILL.md is bound to the code by tests that walk the real parser and constants

**Decision**: `test_skill_md.py` imports `cli.build_parser`, `pending.KINDS/SEVERITIES` and `sources.Source` at test time so the documents cannot name fewer commands, kinds or fields than the code has.

**Rationale**: SKILL.md is what the agent executes from; a stale table is a wrong instruction. Commit 2162bb0 introduced the parser walk after the table had already drifted once.

**Security Scan Note**: These tests read the repo's own files only; no network, no target-project data. This is intentional — see SPEC-030.

## Related Specs

- [SPEC-028: Paths: project root discovery and write containment](./SPEC-028-paths-root-discovery-and-write-containment.md)
- [SPEC-029: Frontmatter: YAML block read/write, atomic save, ISO date normalisation](./SPEC-029-frontmatter-yaml-atomic-save-date-normalisation.md)
- [SPEC-031: Shipped references carry the method, never the law](./SPEC-031-shipped-references-method-never-law.md)
- [SPEC-007: HTTP client: judged redirects, budgets, retries, robots, politeness](../integration/SPEC-007-http-client.md)
- [SPEC-017: CLI dispatch, exit-code contract and refusal boundary (main)](../api/SPEC-017-cli-dispatch-exit-codes.md)
- [SPEC-027: Launcher and preflight: Python ≥ 3.12, PyYAML and a non-empty CA store, or exit 2](../api/SPEC-027-launcher-preflight.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Scan-generated from SKILL.md, the plugin manifests, `bin/compliance-register`, their tests, commits 2162bb0 and 6233e6e, and design decisions D25, D29 |
| 2026-09-20 | Removed BEH-264 (duplicate of SPEC-027 BEH-230, same title and locator) | verify pass |
