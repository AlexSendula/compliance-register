# compliance-register

A register of the laws, guidance, licences and contracts that apply to a
software project — discovered from the sources, quoted and dated, kept in
the repo under `knowledge-base/compliance/`, re-checked on command.

It says what applies, why, and what you must do. It does not verify
compliance and never says "compliant".

## Install

```bash
npx skills add AlexSendula/compliance-register
```

or, in Claude Code:

```
/plugin marketplace add AlexSendula/compliance-register
/plugin install compliance-register@compliance-register
```

Needs Python 3.12+ and PyYAML.

## Use

Ask your agent which regulations apply to the project. It will run the four
stages in `SKILL.md`: profile, discover, register, watch. Commands:

```bash
python3 bin/compliance-register init
python3 bin/compliance-register status
python3 bin/compliance-register search "direct debit mandate"
python3 bin/compliance-register pending
python3 bin/compliance-register resolve chg-0001 --action applied --by "Alex"
python3 bin/compliance-register fetch            # mirror confirmed sources
python3 bin/compliance-register check            # fresh / unreachable / moved → pending
python3 bin/compliance-register rescan           # profile changed? → pending
```

## What it writes

```
knowledge-base/compliance/
  profile.md        the 15 answers
  sources.json      where law lives for your jurisdictions
  mirror/           the text, markdown with provenance frontmatter, one directory per source
  regimes/*.md      one file per regime, obligations inside
  pending.jsonl     detected changes awaiting a human
  resolutions.jsonl what humans did
```

Sources whose licence forbids redistribution go under `mirror/.private/`, which
`init` gitignores; everything else is committed.

The mirror always honours robots.txt. A source it disallows is recorded as
`tier: refuse` and cited by URL instead of fetched; there is no allowlist.

## Design

`design/` in the companion repo `compliance-devkit` holds the workflow,
decisions and research this skill implements.

## Licence

MIT for the tool. Mirrored legal text keeps its source's licence; sources
that forbid redistribution are never committed.
