---
name: review-findings
description: How to review the diff for this feature in a fresh chat and write findings in the fixed JSON format with severity, evidence and a verdict per finding. Use when reviewing a pull request or filling docs/review/findings.json.
---

# Review findings

## Rules of the review
- Use a fresh chat: you must not review your own work from memory. Diff is `git diff <base>..HEAD`.
- Verify every suspicion by reading or running code. At most 12 findings, no praise, no style nits.
- Also look for what is missing: each spec scenario needs a test.

## Checklist
Rules vs spec; state changed before validation; money types; authorisation and roles; thread safety; error mapping; test strength (do refusal tests prove nothing changed?); e2e locators; secrets; docs that no longer match the code (README accounts vs `application.yml`).

## Severity
critical = wrong approval or data change; high = rule bypass or race; medium = weak test, misleading doc, edge case; low = minor; info = observation.

## Output: `docs/review/findings.json`
Array of objects with exactly these keys: `id`, `severity`, `file`, `line`, `title`, `description`, `suggested_fix`, `confidence` (high|medium|low), `unsure_about`, `verdict`, `verdict_reason`, `resolution`. The reviewer sets `verdict` to `pending`. Check with `python scripts/hooks/validate-findings.py docs/review/findings.json`.

## Verdicts (set by the human, afterwards)
- **fixed**: say what changed and how you checked it (`resolution`).
- **dismissed**: say why it is not a real problem (`verdict_reason`).
- **deferred**: say why it waits and what follow-up is needed.
Do not dismiss a valid finding to make the list look finished. Final check: `--final`.
