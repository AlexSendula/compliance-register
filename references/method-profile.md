# Method — stage 1, Profile

Goal: `knowledge-base/compliance/profile.md` with all fifteen answers
`confirmed`. You propose; the human decides (D7).

## Order
1. Ask questions 1 and 2 (`establishment`, `directed_activity`) first and
   wait for the answers. They choose the jurisdictions; nothing else is
   worth asking until they are confirmed.
2. Then the remaining thirteen, in the checklist order.

## For each question
- Read its five lines in `references/dimensions-checklist.md`.
- If **Code may propose** is not "nothing": look in the repository for the
  evidence named there (dependency manifests, schema files, route
  definitions, locale files, environment variable names, SDK imports). Write
  a proposed value and list each piece of evidence as a path plus what it
  showed. Set `status: proposed`.
- The repository name, README and marketing copy are never evidence for
  any answer. Locale files, currencies and store listings are indicia to
  surface under question 2, never a value to assert. The **Trap** line
  tells you the inference to avoid.
- Present the proposal to the human as: the question, your proposed value,
  the evidence, and the trap. Ask them to confirm, correct, or answer
  `unknown`.
- Write the confirmed value with `status: confirmed`. `unknown` stays
  `value: null`, `status: confirmed` — and `profile validate` will report it.
  Do not invent a value to make validation pass.

## Closed lists
`exchanged` is a closed list; pick from the categories in the checklist.
Record the unselected categories in the body under `## Not selected` — they
are what rules out whole regimes later.

## When done
Done is all fifteen `status: confirmed`. Fifteen proposals is not done.

- The human confirms every answer first. Only then ask whose name goes in
  `confirmed_by`, and write it with today's date in `confirmed_at` — never a
  name they did not give, and never while an answer is still `proposed`
  (SKILL.md, "Humans confirm"). `profile validate` reports an attestation
  set early; it cannot tell whether the human actually said it.
- Run `python3 "$SKILL_DIR/bin/compliance-register" profile validate` and
  read every line. `<slug>: proposed, not confirmed` means stage 1 is not
  finished. The one line that is not a to-do is `<slug>: confirmed but value
  is null` — that is an answered `unknown`, and it stays for good, so on a
  profile with one, exit 1 is the finished state. Tell the human when you
  record it: `rescan` refuses on an answered `unknown` (exit 2), so the
  profile-change loop in stage 4 stays shut for this project until that
  answer is known. `check` is unaffected.
- Commit `profile.md`.

## When the profile changes later
Edit the answer, have the human confirm it, update `confirmed_at`, commit,
then run `python3 "$SKILL_DIR/bin/compliance-register" rescan`. It diffs
the confirmed answers against the snapshot the last `rescan` wrote and
raises a `regime-new` or `regime-gone` pending entry per changed dimension;
continue with stage 2b for those dimensions only.
