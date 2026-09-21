# Principles

> The project's constitution: project-wide rules that sit **above** every spec and decision.
> When a spec, decision, or change conflicts with a principle, the principle wins (or the
> principle must be consciously amended). Keep this short — a handful of durable rules, not a
> style guide.

These are the invariants decided in the design repo (`compliance-devkit`,
`design/workflow.md` v0.2 and decisions D1–D29 in `design/brainstorm-2026-09-17.md`).

## How these are enforced

- **Soft (context injection):** this file is auto-injected into the working context of
  brainstorming, planning, and wrap-up, so design happens with the constitution in view.
- **Checkpoint:** wrap-up and code-review diff the change against these principles and raise a
  finding on violation.

## Principles

1. **Router, not oracle.** The register says what applies, why, what you must do and where it
   says so. It never says "compliant" and never tracks whether an obligation was met —
   verification belongs to tests, BDD and other skills. (D1, D15)
   _Why: a register that also judges compliance becomes the thing people trust instead of checking._

2. **Nothing law-specific ships with the skill.** No rule, no threshold, no date, no source
   address. The skill ships the 15 dimension *questions* and the method for finding everything
   else. An `api` adapter may carry only its protocol endpoint. (D4, D5, D17, D28)
   _Why: law changes constantly and differs per jurisdiction; anything hardcoded is wrong on arrival._

3. **Derive, cite, date, cache, confirm.** Every source, regime and obligation is discovered
   from evidence, quoted, dated, stored in the project and confirmed by a human before it
   counts. Code proposes; humans decide. `null` blocks. (D4, D6, D7)
   _Why: an unconfirmed inference presented as fact is worse than no entry._

4. **"Could not reach" is never "not there".** Freshness is three-valued: fresh /
   unreachable / moved. A failed fetch is reported as unreachable, never as absence or change.
   _Why: a research pass once declared a gazette gone because of a User-Agent header._

5. **Commands, not schedules.** The skill offers `check` and `rescan`; when they run is the
   caller's decision. No timers, no cron, no background work. (D16)
   _Why: the project decides its cadence; the skill must not assume one._

6. **Record, surface, delegate.** Detected changes are appended to `pending.jsonl`. Nothing in
   the register moves until a human resolves the entry. Logs are append-only. (D19, D26)
   _Why: auto-applied changes to a compliance register are unauditable._

7. **Code in the skill, data in the project.** Profile, sources config, mirrored text and the
   register live under `knowledge-base/compliance/` in the target project, committed and
   licence-gated; non-redistributable text goes to `mirror/.private/` and is git-ignored. (D20, D23)
   _Why: the register is part of the project's history, not of the tool's._

8. **robots.txt and disallows are always honoured.** Read per RFC 9309 (redirects followed;
   4xx = no rules; 5xx or unreachable = rules unknown, so the host is unreachable), evaluated
   against this tool's own product token whatever User-Agent the request carries, with no bypass
   and no allowlist. A per-source `user_agent` policy may be recorded by a human for hosts that
   reject non-browser clients; it never changes which robots rules apply. A refused source is
   reported as refused. (D24)
   _Why: the tool scrapes regulators; it must be a good citizen or it will be blocked for everyone._

9. **Refuse loudly, never brick.** A guard, a bad file or an unreachable host produces a clear
   message and a non-zero exit; a poisoned data file never prevents another command from
   running, and nothing raises inside the loop over sources.
   _Why: the failure mode of a compliance tool must be "it told me", never "it silently skipped"._

10. **Escape at the sink.** Mirrored text is untrusted. Everything printed to a terminal passes
    through `render.printable`; every path component passes through `paths.safe_component` and
    containment. (docs-mirror ADR-008)
    _Why: a regulator's page can contain anything, including terminal escapes and `../`._

11. **Stdlib + PyYAML, Python ≥ 3.12, no network in tests.** No new runtime dependency without
    a decision here; every HTTP interaction is injectable and tested against a fake opener.
    _Why: the skill is dropped into other people's projects; its footprint must stay tiny and its tests deterministic._

## Change history

| Date | Change |
|------|--------|
| 2026-09-20 | Initial constitution, transcribed from `design/workflow.md` invariants and D1–D29. |
| 2026-09-21 | P8 reworded: the transcription said "no browser impersonation", which contradicted the design's per-source UA policy (workflow.md, brainstorm error #2). Scoped to what D24 decided — robots rules, RFC 9309 reading, evaluated against our own token under every UA. |
