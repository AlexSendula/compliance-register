# compliance-register — knowledge base

Documentation, specs, decisions and governance artifacts for the compliance-register skill.
Generated and maintained by freya-devkit (`AGENTS.md`); regenerate with `/freya-devkit:freya-wrap-up`.

## Reference docs

| Document | Description |
|----------|-------------|
| [Project Overview](./reference/PROJECT_OVERVIEW.md) | What the skill is, who it is for, the four stages, the invariants |
| [Architecture](./reference/ARCHITECTURE.md) | Module map, command → module → file flow, on-disk layout, design decisions |
| [CLI Reference](./reference/API.md) | Every subcommand, its options, exit codes, and the file formats it reads and writes |
| [Developer Guide](./reference/DEVELOPER.md) | Setup, local install, adding an adapter or subcommand, commit conventions |
| [Testing](./reference/TESTING.md) | pytest layout, the no-network rule, FakeOpener, fixtures, what is not tested |
| [Style Guide](./reference/STYLE_GUIDE.md) | Python and markdown conventions actually used in the code |
| [Security](./reference/SECURITY.md) | Threat model, SSRF/robots/path/escape controls, known limitations |
| [Troubleshooting](./reference/TROUBLESHOOTING.md) | Exit codes and messages, and what to do about each |
| [Publishing & Release](./reference/DEPLOYMENT.md) | Distribution channels, release checklist, version locations |

## Governance

| Artifact | Owner | Purpose |
|----------|-------|---------|
| [principles.md](./principles.md) | spec-manager | The constitution — 11 invariants from the design decisions D1–D29 |
| [specs/](./specs/README.md) | spec-manager | Per-feature intent, intentional decisions, proposed behaviors |
| [decisions/](./decisions/README.md) | spec-manager | Cross-cutting ADRs |
| [security/](./security/) | codebase-security-scan | Security findings |
| [BACKLOG.md](./BACKLOG.md) | status | Generated outstanding-work list — never hand-edit |

## Reading order

1. [PROJECT_OVERVIEW.md](./reference/PROJECT_OVERVIEW.md) — what it does and, more importantly, what it refuses to do
2. [principles.md](./principles.md) — the rules every change is judged against
3. [ARCHITECTURE.md](./reference/ARCHITECTURE.md) — how the pieces fit
4. [DEVELOPER.md](./reference/DEVELOPER.md) — run the tests, try it on a scratch project
5. [API.md](./reference/API.md) — the command surface

The design history (brainstorm, decisions, workflow v0.2, plans A/B, research) lives in the sibling
repo `compliance-devkit`; the register's own data lives in each target project under
`knowledge-base/compliance/`, not here.
