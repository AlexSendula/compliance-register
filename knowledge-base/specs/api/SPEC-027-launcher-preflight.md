---
id: SPEC-027
title: 'Launcher and preflight: Python ≥ 3.12, PyYAML and a non-empty CA store, or exit 2'
category: api
tags: [api, launcher, preflight, D29, principle-4, principle-11]
status: implemented
certainty: 90
created: 2026-09-20
updated: 2026-09-20
related_code:
  - bin/compliance-register
  - compliance_register/preflight.py
  - compliance_register/cli.py
  - tests/test_launcher.py
  - tests/test_preflight.py
intentional_decisions:
  - "Prerequisite failures exit 2, not 1, and are printed as an installable list"
  - "The launcher edits sys.path instead of requiring an install"
  - "The version guard runs before any package import and uses %-formatting"
  - "preflight checks the CA store even though no network is touched at start-up"
behaviors:
  - behavior_id: BEH-229
    title: 'The launcher, run via subprocess with --version, exits 0 and prints ''compliance-register <version>'''
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_launcher.py::test_launcher_prints_version
  - behavior_id: BEH-230
    title: 'bin/compliance-register has the executable bit set'
    state: proposed
    level: component
    adapter: pytest
    locator: tests/test_launcher.py::test_launcher_is_executable
  - behavior_id: BEH-231
    title: 'An empty CA trust store yields a problem mentioning ''no CA certificates'' and SSL_CERT_FILE; a populated store yields none'
    state: proposed
    level: unit
    adapter: pytest
    locator: tests/test_preflight.py::test_empty_trust_store_is_named
  - behavior_id: BEH-232
    title: 'A missing yaml module yields a problem containing the pip install command'
    state: proposed
    level: unit
    adapter: pytest
  - behavior_id: BEH-233
    title: 'When check_prerequisites returns problems the launcher prints ''compliance-register cannot start:'' with one ''  - '' line each and exits 2 without importing cli'
    state: proposed
    level: component
    adapter: pytest
  - behavior_id: BEH-234
    title: 'On Python older than 3.12 the launcher exits 2 with the found version in the message'
    state: proposed
    level: component
    adapter: pytest
---

# Launcher and preflight: Python ≥ 3.12, PyYAML and a non-empty CA store, or exit 2

## What

`bin/compliance-register` is an executable Python script with no install step. It first checks `sys.version_info < (3, 12)` and exits 2 with `compliance-register needs Python 3.12 or newer (found X.Y)` on stderr, using %-formatting so the message is reachable on any older interpreter that can parse the file. It resolves its own path with `os.path.realpath` (skill installers symlink the directory), inserts the repository root at the front of `sys.path`, and imports `compliance_register.preflight`.

`preflight.check_prerequisites()` returns a list of human-readable problems and must not raise: PyYAML missing (via `importlib.util.find_spec('yaml')`, with the pip command to run) and an empty Python CA trust store (`ssl.create_default_context().cert_store_stats()['x509_ca'] == 0`, naming the macOS `Install Certificates.command` and the certifi/`SSL_CERT_FILE` route). A non-empty list is printed under `compliance-register cannot start:` and the launcher exits 2 before `cli` is imported. Otherwise `cli.main()`'s return becomes the process exit.

## Why

SKILL.md tells the agent to invoke the CLI by path and, on exit 2 with a named prerequisite, to tell the user rather than work around it. D29 classes a missing dependency as refused (2). Principle 11 fixes the footprint at stdlib + PyYAML and Python ≥ 3.12, so those are the only things checked.

The CA check exists because an empty trust store makes every https fetch fail, which `check` would honestly report as unreachable for every source. Principle 4 says that is never "not there", but a whole register of "unreachable" would still mislead; naming the cause up front (commit d84b52a) is cheaper than diagnosing it after the first run.

Open question: the Python-too-old path and the PyYAML-missing path have no test (they would need a second interpreter or module shadowing); confirm that is accepted coverage.

## Behavior

The observable acceptance behavior is owned by each behavior's **test**, not by
this spec — link to it here, never copy the scenario steps (single source of
truth). Add one row per `BEH-NNN` in the frontmatter `behaviors:` list.

| Behavior | State | Verified by |
|----------|-------|-------------|
| BEH-229 The launcher, run via subprocess with --version, exits 0 and prints 'compliance-register <version>' | proposed | `tests/test_launcher.py::test_launcher_prints_version` |
| BEH-230 bin/compliance-register has the executable bit set | proposed | `tests/test_launcher.py::test_launcher_is_executable` |
| BEH-231 An empty CA trust store yields a problem mentioning 'no CA certificates' and SSL_CERT_FILE; a populated store yields none | proposed | `tests/test_preflight.py::test_empty_trust_store_is_named` |
| BEH-232 A missing yaml module yields a problem containing the pip install command | proposed | — (test owed) |
| BEH-233 When check_prerequisites returns problems the launcher prints 'compliance-register cannot start:' with one '  - ' line each and exits 2 without importing cli | proposed | — (test owed) |
| BEH-234 On Python older than 3.12 the launcher exits 2 with the found version in the message | proposed | — (test owed) |

## Intentional Design Decisions

### Prerequisite failures exit 2, not 1, and are printed as an installable list

**Decision**: The launcher prints one `  - <problem>` line per prerequisite and exits 2 before importing the CLI.

**Rationale**: D29: missing dependency is a refusal. The list format lets an agent read exactly what to install; SKILL.md forbids working around it.

**Security Scan Note**: n/a

### The launcher edits sys.path instead of requiring an install

**Decision**: The directory above `bin/` is inserted at `sys.path[0]` after `realpath`.

**Rationale**: The skill is dropped into other people's projects (git clone, `~/.agents/skills`, plugin cache) and installers symlink it; an install step would be one more thing to fail. `realpath` is needed so the symlinked `bin` resolves to the real package.

**Security Scan Note**: `sys.path[0]` insertion of the skill's own directory is the intended import mechanism, not a path-hijack vector; the path is derived from `__file__`, not from user input.

### The version guard runs before any package import and uses %-formatting

**Decision**: The Python check is the first statement and avoids f-strings/newer syntax in that line.

**Rationale**: On an interpreter older than 3.12 the package may fail to parse (PEP 604 unions, dataclass features); the guard must print its message before anything else is imported.

**Security Scan Note**: n/a

### preflight checks the CA store even though no network is touched at start-up

**Decision**: An empty `x509_ca` count is treated as a start-up refusal, not deferred until the first fetch.

**Rationale**: Every https fetch would fail identically and be reported as unreachable per source; the root cause is a machine setup issue best named once, up front, with the fix command.

**Security Scan Note**: n/a

## Related Specs

- [SPEC-017: CLI dispatch, exit-code contract and refusal boundary](./SPEC-017-cli-dispatch-exit-codes.md)
- [SPEC-030: Packaging: SKILL.md contract, plugin manifests, path launcher and version](../infra/SPEC-030-packaging-skill-md-plugin-launcher-version.md)

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-09-20 | Initial spec | Generated from codebase scan by freya-spec-manager |
