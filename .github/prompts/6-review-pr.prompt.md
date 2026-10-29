---
description: Step 6. Review the diff and write findings in a fixed JSON format. Use a FRESH chat.
mode: agent
---
Review this PR against our checklist. Report findings by severity with file and line, suggest a fix for each, and say what you are unsure about.

## Before you start
You must be in a FRESH chat. If this chat contains earlier implementation work, stop and tell me to open a new one. Use `git diff <base>..HEAD` (find the base with `git log --oneline`).

## Skills (open the file if your Copilot does not load it for you)
- `review-findings` (`.github/skills/review-findings/SKILL.md`): checklist, severity, JSON format, verdicts
- `approval-rules` (`.github/skills/approval-rules/SKILL.md`): the traps to look for

## How
- Follow skill `review-findings` (checklist, severity, what to verify). Verify each suspicion by reading or running code; at most 12 findings, no praise, no style nits.
- Also look for what is MISSING: every spec scenario needs a test; list any that has none.

## Output
Write ONLY `docs/review/findings.json`: an array of objects with exactly these keys: `id`, `severity` (critical|high|medium|low|info), `file`, `line`, `title`, `description`, `suggested_fix`, `confidence` (high|medium|low), `unsure_about`, `verdict`, `verdict_reason`, `resolution`. Set every `verdict` to "pending". Run `python scripts/hooks/validate-findings.py docs/review/findings.json` and fix format errors.

## Rules
Do not edit source files. I set each verdict myself: fixed, dismissed (with reason) or deferred (with reason).

## Done when
The validator passes; your reply lists findings by id, severity and title.

## Finish (in this order; details in "Finish protocol" in `.github/copilot-instructions.md`)
1. Log: `python scripts/ai_log.py add --prompt-ref 6-review-pr --action "<one per real thing you did>" --tool-used "<only tools that ran>" --command-run "python scripts/hooks/validate-findings.py docs/review/findings.json"`
2. Commit: `git add -A`, then `git commit -m "docs: add review findings" -m "Why: the diff was reviewed in a fresh chat and every finding needs a verdict"`. Adjust the wording to what you really changed. Skip if only `docs/ai-log/` changed.
3. Tell me the commit hash and message.
