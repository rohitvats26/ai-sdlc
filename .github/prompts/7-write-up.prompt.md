---
description: Step 7. Fill in ASSIGNMENT.md and the PR description from real evidence.
mode: agent
---
Goal: an honest write-up. Every claim needs evidence.

## Before you start (stop and tell me if a check fails)
`python scripts/hooks/validate-findings.py --final docs/review/findings.json` passes (a verdict on every finding). Then run `python scripts/evidence.py` and use its output as your facts: commits, test counts, mutation scores, findings tally, AI log summary.

## Read only these
`ASSIGNMENT.md`, `README.md`, `docs/`, `openspec/`, and the `evidence.py` output.

## Do
- Fill the traceability table in `ASSIGNMENT.md`: for each requirement, what was built, the evidence (file path, commit hash or command output) and a status (Completed, Partially completed, Not completed, Pending).
- Paste the PIT scores before and after as text.
- Write `docs/PULL_REQUEST.md`: summary, business-rule coverage, test results, mutation scores, AI tools used (from the AI log), the review findings table with verdicts, known limits and open assumptions.
- Check `README.md` against the code (accounts and roles match `application.yml`, rules match what was built, test commands work) and fix any mismatch.

## Rules
Only state a result you can show. Otherwise mark it Pending. Never invent numbers, commit hashes or links; the demo video and the PR link stay Pending until I add them. Do not tidy the AI log: it records what really happened, including Copilot's mistakes. Short, plain sentences.

## Done when
No table cell is empty and every "Completed" has evidence next to it.

## Finish (in this order; details in "Finish protocol" in `.github/copilot-instructions.md`)
1. Log: `python scripts/ai_log.py add --prompt-ref 7-write-up --action "<one per real thing you did>" --tool-used "<only tools that ran>"`
2. Commit: `git add -A`, then `git commit -m "docs: complete assignment write-up" -m "Why: the write-up maps every requirement to evidence"`. Adjust the wording to what you really changed. Skip if only `docs/ai-log/` changed.
3. Tell me the commit hash and message.
