---
description: Step 1. Check the baseline, then write the OpenSpec change for approval limits by role. No code.
mode: agent
---
Goal: a validated spec for approval limits by role. Spec only, no code.

## Before you start (stop and tell me if a check fails)
- Run `mvn test`. Note: `Baseline: <N> tests, <pass/fail>`. If it is red, stop.
- `openspec --version` works. If not, tell me to run `npm i -g @fission-ai/openspec`.

## Read only these
"Feature being built" in `AGENTS.md`, `src/main/java/**` (skim), `src/test/java/**` (skim), `application.yml`.

## Skills (open the file if your Copilot does not load it for you)
- `approval-rules` (`.github/skills/approval-rules/SKILL.md`): the rules table and traps
- `openspec-propose` (`.github/skills/openspec-propose/SKILL.md`): how to create the OpenSpec change

## Plan first (in the chat)
Max 8 bullets: the requirements you will write and every ambiguity you found.

## Do
- Use OpenSpec to create the change `add-approval-limits-by-role`: proposal, specs, design, tasks.
- Requirements (each uses SHALL, each has WHEN/THEN scenarios): Manager limit (up to 50,000); Director limit (up to 500,000); two distinct approvers above 500,000, the second a Director; same user never counts twice; a refused attempt returns a clear reason and changes nothing (status, amount, decision fields, history); input checks (blank approver, unknown role, invalid amount); approval history (who, role, when, in order).
- Boundary scenarios: 50,000, 50,000.01, 500,000, 500,000.01. API: refusal is HTTP 403 with `{ "error": reason }`.
- `design.md`: per ambiguity write the question, options, the safe option you chose, the consequence. Include at least: may a Manager be first approver above 500,000? Does "same user" ignore case? What happens to the `Approver` and `Admin` roles and `demo.approver`? Add a table: requirement to planned test class.
- `tasks.md` in groups, each task with a "verify" line: (1) single-approver limits, (2) two-approver rule, (3) UI and Playwright, (4) mutation testing and review.

## Rules
Do not touch `src/`. Do not invent rules that are not in `AGENTS.md`; write them as questions.

## Done when
- `openspec validate add-approval-limits-by-role --strict` passes (show it); every requirement has a scenario.
- Reply with `{"baseline":"<N tests, pass>","assumptions":[],"open_questions":[],"validated":true}`.

## Finish (in this order; details in "Finish protocol" in `.github/copilot-instructions.md`)
1. Log: `python scripts/ai_log.py add --prompt-ref 1-spec --action "<one per real thing you did>" --tool-used "<only tools that ran>" --run-tests "mvn -q test" --command-run "openspec validate add-approval-limits-by-role --strict"`
2. Commit: `git add -A`, then `git commit -m "docs: spec for approval limits by role" -m "Why: the spec is written and validated before any code, so every later step has a source of truth"`. Adjust the wording to what you really changed. Skip if only `docs/ai-log/` changed.
3. Tell me the commit hash and message.
