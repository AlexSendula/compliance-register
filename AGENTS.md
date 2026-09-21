<!-- freya-devkit:begin (managed by `freya init` — edits inside are overwritten) -->

## freya-devkit

This project uses the freya-devkit skill suite. Its skills are installed for
your agent under their own names, and its tools are reached through one launcher.

- `freya <command>` (a space) is the CLI — for example `freya code-graph --build`.
  Run `freya help` for the full list. Do not call the bundled scripts by path,
  and never with a bare `python`.
- `freya-<skill>` (a hyphen) is a skill name. Skills refer to each other this way.
- Generated artifacts — documentation, specs, security reports — are committed
  separately from the code change that prompted them: the two-commit pattern.
- Where a skill fans work out across several independent tasks, run them in
  parallel if your agent supports subagents, and one at a time if it does not.

| Skill | Use it for |
|---|---|
| `freya-behavior-graph` | Own behavior.json (the BEHAVIOR -> TEST -> CODE projection) and answer the two blast-radius directions: code change -> affected behaviors, and behavior -> implementing code. |
| `freya-behavior-runner` | Run a project's accepted behaviors via their adapter and capture observed coverage as TEST -> CODE fingerprints. |
| `freya-code-graph` | Build and query code dependency graphs for impact analysis and blast radius tracking. |
| `freya-codebase-security-resolver` | Resolve security findings from the codebase security scan interactively. |
| `freya-codebase-security-scan` | Performs a comprehensive security audit of an entire codebase. |
| `freya-dependency-vulnerability-check` | Scans project dependencies for security vulnerabilities using npm audit, yarn audit, or pnpm audit. |
| `freya-docs-manager` | Manages all project documentation in a standardized `knowledge-base/` directory structure. |
| `freya-spec-manager` | Create and manage feature specifications that capture intentional design decisions. |
| `freya-status` | Read-only project status: aggregate outstanding behavior/coverage/security work (behaviors to confirm, tests owed, coverage gaps, open security findings) and refresh the git-tracked knowledge-base/BACKLOG.md. |
| `freya-wrap-up` | Complete your feature implementation workflow by running all post-implementation tasks in sequence: update dependency graph, update docs, update specs, run security scan, and commit everything together. |

<!-- freya-devkit:end -->
