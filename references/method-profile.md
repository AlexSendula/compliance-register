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
- Never use the repository name, README, marketing copy, or a locale file's
  existence as evidence for questions 1–6. The **Trap** line tells you the
  inference to avoid.
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
- Set `confirmed_by` and `confirmed_at`.
- Run `python3 "$SKILL_DIR/bin/compliance-register" profile validate`.
- Commit `profile.md`.

## When the profile changes later
Edit the answer, update `confirmed_at`, commit, then run
`python3 "$SKILL_DIR/bin/compliance-register" profile diff --against HEAD~1`
and continue with stage 2 for the dimensions it lists.
