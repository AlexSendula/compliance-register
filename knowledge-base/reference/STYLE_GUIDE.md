# Style Guide

> Last updated: 2026-09-22

Conventions as they are actually practised in `compliance_register/`, `tests/`, `SKILL.md` and `references/`. Nothing here is aspirational: every rule below is one the code already follows, with the line that shows it. There is no linter, formatter or pre-commit hook in this repo (`pyproject.toml:1-15` holds only project metadata and pytest options; `requirements-dev.txt:1-2` is `pytest` and `PyYAML`) — the tests are the only enforcement, and some of them enforce documentation rules (`tests/test_skill_md.py`).

## General principles

1. **Refuse loudly, never silently.** A guard that stops a fetch says why in the result; nothing is swallowed. `compliance_register/mirror/adapters/eurlex.py:185-196` names each guard `G1`–`G5` in the refusal string.
2. **One bad row or source never denies the rest.** Loops over sources catch everything per iteration (`compliance_register/check.py:55-59`, `compliance_register/fetch.py:37-40`); corrupt lines are skipped and counted, not raised (`compliance_register/pending.py:22-40`).
3. **"Could not reach" is not "no change".** `HttpRefused` (we chose not to) and `HttpUnreachable` (we tried and failed) are distinct classes with one-line docstrings saying when each applies (`compliance_register/mirror/http.py:40-45`); a retry exhausted is unreachable, never fresh (`compliance_register/mirror/http.py:122-139`).
4. **Comments say why, and cite the decision.** `(D17)`, `(D19)`, `(D24)` in module docstrings point at the design repo's brainstorm decisions (`compliance_register/sources.py:1-3`, `compliance_register/pending.py:1`, `compliance_register/mirror/http.py:5`); docs-mirror findings are cited as `SEC-049/050` (`tests/test_poisoned_files_do_not_brick.py:1-2`).

## Python

### Runtime and dependencies

Python >= 3.12, stdlib plus PyYAML, nothing else (`pyproject.toml:4-5`). The launcher refuses older interpreters with exit 2 (`bin/compliance-register:9-14`) and `preflight.check_prerequisites` names a missing PyYAML or an empty CA store rather than letting the first import or fetch fail (`compliance_register/preflight.py:9-16`). Do not add a dependency; `render.py` exists precisely because a sink guard "that depended on anything could be defeated by changing that thing" (`compliance_register/render.py:26-28`).

### Module layout

Every module opens with a docstring stating what the file owns, then `from __future__ import annotations`, then stdlib imports, a blank line, then package-relative imports (`compliance_register/paths.py:1-10`, `compliance_register/mirror/http.py:1-17`, `compliance_register/mirror/store.py:1-13`). The docstring often states an ownership rule: "The only module allowed to decide a path" (`compliance_register/paths.py:1`), "the only module that reads or writes the block" (`compliance_register/frontmatter.py:1-2`), "Terminal I/O and exit codes only; all logic lives in the other modules" (`compliance_register/cli.py:1-2`).

Colliding names are imported under short aliases: `frontmatter as fm`, `check as checkmod`, `sources as srcmod`, `http as _http` (`compliance_register/cli.py:11-13`, `compliance_register/check.py:9`, `compliance_register/fetch.py:6-7`). Import cycles are broken with a lazy import and a comment naming the cycle (`compliance_register/sources.py:95`, `compliance_register/fetch.py:27`, `compliance_register/mirror/adapters/__init__.py:33`).

Module constants are `UPPER_SNAKE`; closed vocabularies are tuples, not enums, and validation checks membership in them (`compliance_register/sources.py:17-20`, `compliance_register/pending.py:11-13`, `compliance_register/regimes.py:12-14`). Module-private regexes and state carry a leading underscore: `_SAFE` (`compliance_register/paths.py:15`), `_CONTROL` and `_LAST_BY_HOST` (`compliance_register/mirror/http.py:24-27`), `_HEADER`/`_CONSOL`/`_ISO` (`compliance_register/mirror/adapters/eurlex.py:22-27`).

Code copied from docs-mirror keeps a two-line header saying so and forbidding local edits (`compliance_register/render.py:1-2`).

### Naming

| Thing | Convention | Where |
|---|---|---|
| Module | one lowercase word: `paths`, `pending`, `store`, `htmlmd` | `compliance_register/` |
| CLI handler | `cmd_<command>` / `cmd_<group>_<sub>`, returns `int` | `compliance_register/cli.py:22`, `compliance_register/cli.py:91`, `compliance_register/cli.py:127` |
| Exception | `<Condition>` noun phrase, one-line docstring saying when | `compliance_register/paths.py:18-23`, `compliance_register/sources.py:24-25` |
| Record | `@dataclass` with `field(default_factory=...)` for mutables | `compliance_register/sources.py:28-49`, `compliance_register/mirror/adapters/__init__.py:14-29` |
| Compliance dir | `cdir: Path` everywhere; `_cdir()` in the CLI | `compliance_register/cli.py:18-19`, `compliance_register/check.py:37` |
| Report dict | `rep` with an `"exit"` key the CLI returns | `compliance_register/check.py:40`, `compliance_register/fetch.py:20`, `compliance_register/cli.py:147` |
| Problem list | `problems` / `p: list[str]` of `"<id>: <what>"` strings | `compliance_register/sources.py:72-101`, `compliance_register/cli.py:129` |
| Loop variables | `s` for a source, `r` for a result or regime, `e` for an entry | `compliance_register/check.py:55-77`, `compliance_register/pending.py:83-84` |

### Options are keyword-only; test seams are parameters

Anything after the required positionals sits behind `*`: `Http(*, user_agent, delay_seconds, timeout, max_bytes, opener, sleep)` (`compliance_register/mirror/http.py:71-72`), `get(url, *, allowed_hosts, max_bytes)` (`compliance_register/mirror/http.py:142`), `write_page(..., *, retrieved_at)` (`compliance_register/mirror/store.py:31`), `pending.add(..., *, source, affects, extra, now)` (`compliance_register/pending.py:58-59`). The same signature is the test seam: `opener=` and `sleep=` replace the network and the clock (`tests/test_http.py:9-10`), `client_factory=` replaces the HTTP client in `check.run`/`fetch.run` (`compliance_register/check.py:37`, `compliance_register/fetch.py:17`), `today=`/`now=` replace the date. No monkeypatching of module globals is needed for the common cases.

### Records and validation

Data files map to dataclasses with `from_dict` / `to_dict` that drop unknown keys and normalise shape (`compliance_register/sources.py:51-65`). Validation never raises: `sources.validate` returns `list[str]` (`compliance_register/sources.py:72-101`), a `Regime` carries its own `problems` list (`compliance_register/regimes.py:39`), and `sources.refusals` folds validation into a `{id: reason}` dict that `check`/`fetch` consult before any request (`compliance_register/sources.py:104-115`, `compliance_register/check.py:46-50`). Only an unreadable *file* raises — `SourcesError` (`compliance_register/sources.py:133-141`), `FrontmatterError` (`compliance_register/frontmatter.py:29-36`) — and `main()` turns those into exit 1.

### Errors and exit codes

```mermaid
flowchart LR
    A[cmd_* handler] -->|returns int| X0["0 done"]
    A -->|rep['exit']| X1["1 failure"]
    A -->|rep['exit']| X2["2 refused"]
    B[NotAProject / UnsafePath] -->|main: 'refused: …'| X2
    C[FrontmatterError / SourcesError] -->|main: 'error: …'| X1
    D[argparse SystemExit] -->|main| X1
    E[bin launcher: old Python, missing PyYAML, no CA store] --> X2
```

`main()` is the only place exceptions become exit codes (`compliance_register/cli.py:224-243`); handlers return `int` and logic modules return `rep["exit"]` set in place (`compliance_register/check.py:41-50`, `compliance_register/check.py:78-79`, `compliance_register/fetch.py:22-26`, `compliance_register/fetch.py:45`). argparse's own exit 2 on a bad argument is remapped to 1 because 2 means "refused" here (`compliance_register/cli.py:228-229`). The launcher exits 2 before the package is imported when a prerequisite is missing (`bin/compliance-register:21-26`).

### Never raise inside a loop over sources

Per-source work is wrapped so that one failure becomes a result and the run continues to `srcmod.save` (`compliance_register/check.py:55-59`, `compliance_register/fetch.py:37-40`); the eurlex prefetch that runs before the loop is guarded the same way and surfaces its failure per source (`compliance_register/mirror/adapters/__init__.py:38-50`). Readers of project files follow the same rule — `pending._read` skips and counts a corrupt line (`compliance_register/pending.py:22-40`), `store.load_manifest` returns `{}` on anything unreadable (`compliance_register/mirror/store.py:54-64`). `tests/test_poisoned_files_do_not_brick.py` is the regression suite for this rule.

### Escape at the sink

Every CLI line that prints text the tool did not write goes through `render.printable` (`compliance_register/render.py:48-88`): pending rows (`compliance_register/cli.py:61`), search hits (`compliance_register/cli.py:87`), validator problems (`compliance_register/cli.py:98`, `compliance_register/cli.py:131`, `compliance_register/cli.py:138`), per-source details (`compliance_register/cli.py:146`, `compliance_register/cli.py:157`) and exception messages (`compliance_register/cli.py:236-242`). Wrap with `printable(str(x))` when the value may not be a string. `!r` is fine for a single URL or name in a refusal message (`compliance_register/paths.py:52`, `compliance_register/sources.py:79`) and wrong for prose (`compliance_register/render.py:59-66`). `render.py` has no imports by design — do not add any.

### Writing files

Whole-file writes are atomic: `tempfile.mkstemp` in the target directory, `os.replace`, and a `finally` that unlinks a leftover temp file (`compliance_register/frontmatter.py:64-73`, `compliance_register/sources.py:144-155`, `compliance_register/mirror/store.py:67-79`). JSONL files are append-only and state is derived by replay (`compliance_register/pending.py:1-4`, `compliance_register/pending.py:52-55`). Every open uses `encoding="utf-8"` and, for writes, `newline="\n"`; JSON is dumped with `indent=2` and a trailing newline.

### Paths

`paths.py` decides every path. A name from a source, a regime id or the command line passes `safe_component` (ASCII, no leading dot, no separators — `compliance_register/paths.py:15`, `compliance_register/paths.py:48-53`) and the final target passes `contained(base, target)` (`compliance_register/paths.py:38-45`) before a write. `store.source_dir` and `store.write_page` are the reference use (`compliance_register/mirror/store.py:18-24`, `compliance_register/mirror/store.py:31-33`). Nothing is written outside `<root>/knowledge-base/compliance/`.

### Dates

Dates are `YYYY-MM-DD` strings and are compared as strings (`compliance_register/check.py:33`, `compliance_register/check.py:86`). The CLI's `--today` is validated to that shape (`compliance_register/cli.py:176-182`), `frontmatter.loads` turns PyYAML's date objects back into strings once, at the boundary (`compliance_register/frontmatter.py:43-52`), and `pending._today` defaults `now` (`compliance_register/pending.py:18-19`). The one timestamp (`.last-check`) is written as `<date>T<HH:MM:SS>Z` (`compliance_register/check.py:82`).

### Formatting

Four-space indent, double quotes throughout, no line-length limit (a lookup table runs to 320 columns, `compliance_register/mirror/adapters/eurlex.py:19`). Two idioms that a formatter would undo are deliberate: `;`-joined one-liners when building argparse subcommands (`compliance_register/cli.py:192-220`) and `append(...); return` guard lines (`compliance_register/mirror/adapters/eurlex.py:185-196`). Comments sit at line end or on the line above and explain a non-obvious *why* (`compliance_register/sources.py:57`, `compliance_register/mirror/http.py:22-27`, `compliance_register/mirror/store.py:34`). Do not add Black, Ruff or a line limit unless the whole tree is reformatted in one commit; nothing here recommends a tool the repo does not use.

## Tests

- `tests/test_<module>.py` mirrors the module; adapters are `test_adapter_<name>.py`; cross-cutting suites are named for the property (`test_poisoned_files_do_not_brick.py`, `test_skill_md.py`, `test_launcher.py`).
- A test name is a sentence about behaviour, not a function name: `test_check_unreachable_is_info_never_fresh` (`tests/test_check.py:38`), `test_robots_has_no_bypass_switch` (`tests/test_http.py:65`), `test_validation_problem_exits_2_before_any_request` (`tests/test_fetch.py:32`).
- One shared fixture, `project` — a tmp dir with an empty `knowledge-base/` (`tests/conftest.py:5-9`). Each file defines its own small `client()` / `write()` helper and module-level sample dicts (`EURLEX`, `META`) that other files import (`tests/test_http.py:9-10`, `tests/test_poisoned_files_do_not_brick.py:9-12`).
- No network, ever: `tests/fakehttp.py` routes `url → (status, headers, body)` with a trailing `*` prefix match and records every request (`tests/fakehttp.py:8-26`). `@pytest.mark.parametrize` is used for value sets (`tests/test_sources.py:69`).
- Run: `python3 -m pytest -q` from the repo root; 315 tests, under a second (`pyproject.toml:13-15`).

## Markdown

### `SKILL.md`

Frontmatter fields, in order: `name`, `description` (block scalar, ends with a `TRIGGER when:` clause), `license`, `compatibility`, `metadata.author`, `metadata.version` (`SKILL.md:1-21`). `tests/test_skill_md.py:16-24` enforces the name regex and length, description <= 1024 chars containing `TRIGGER when`, `license: MIT`, and under 500 lines; `:39-42` requires every `references/*.md` link to exist. The body is tables with `|---|---|` rules, `—` and `·` as separators, commands in backticks.

### `references/*.md`

No frontmatter. Method files are titled `# Method — stage N, Name` and open with `Goal: …` citing decisions (`references/method-profile.md:1-4`). Shipped references and docs carry the method, never the law: `tests/test_skill_md.py:55-59, 128-137` greps them for CELEX numbers, ISO dates, `Art. N` citations and URLs and fails on any. `method-discover-sources.md` must name every agent-written `Source` field and every `KINDS`/`TIERS`/`STATUSES` value in backticks (`tests/test_skill_md.py:73-80`). `regime-template.md` uses `<angle-bracket>` placeholders and `EXAMPLE` ids only (`references/regime-template.md:15-51`).

### The word "compliant"

Never written as a verdict — not in `SKILL.md` (`tests/test_skill_md.py:27-29`), not in a regime file (`references/regime-template.md:58`), not in this documentation.

## Git

Commit subjects follow `type(scope): lowercase description` — `fix(sitemap): cap fan-out at 2000 pages…`, `docs(skill): …`, `test(docs): …`, `feat(preflight): …` — and read as a sentence about behaviour, the same voice as test names. Generated `knowledge-base/` artifacts go in a separate commit from the code that prompted them (`AGENTS.md:12-13`). Development happens on `main`.

## Related documentation

- `SKILL.md` — the operator-facing contract this style serves
- `references/regime-template.md` — the file shape the register produces
- `knowledge-base/reference/` — sibling reference docs written by the docs manager
