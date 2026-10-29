---
description: Step 3. Two distinct approvers above 500,000 (task group 2).
mode: agent
---
Goal: task group 2 of the spec only.

## Before you start (stop and tell me if a check fails)
Step 2 is committed, `mvn test` is green, and `design.md` records the decision about the first approver above 500,000. Follow it.

## Read only these
The spec scenarios for the two-approver rule, `design.md`, `AGENTS.md`, and the domain and test code from step 2.

## Skills (open the file if your Copilot does not load it for you)
- `approval-rules` (`.github/skills/approval-rules/SKILL.md`): rules, design and traps
- `approval-tests` (`.github/skills/approval-tests/SKILL.md`): refusal and concurrency test recipes

## Plan first (in the chat)
The cases you will cover and the classes you will change.

## Build
- Above 500,000 the invoice stays `PENDING_APPROVAL` after the first approval and records it. The second approver must be a Director. The same user never counts twice (trimmed, ignoring case). Only the second valid approval sets Approved, `decidedBy` and `decidedAt`.
- Expose approvals recorded and required in the JSON. Run approve and reject under one lock so two requests cannot both pass the checks.
- Update `README.md`: the approval limits section now includes the two-approver rule and which accounts are first and second approver.

## Tests
First approval leaves it pending with one record; a second, different Director completes it with the history in order; a Manager as second approver is refused ("second approver must be a Director"); the same user twice is refused, including `Demo.Director` and `  demo.director `; every refusal proves the invoice is unchanged (snapshot); an approved invoice cannot be approved again; simultaneous requests by one user record exactly one approval. The concurrency test must fail without the lock (recipe in skill `approval-tests`).

## Rules
Same as step 2. If a test still fails after 3 attempts, stop and tell me.

## Done when
`mvn test` passes; a table (spec requirement of group 2 to its test); you briefly removed the lock, saw the concurrency test fail, and put the lock back (say so). Do NOT change the UI or the spec.

## Finish (in this order; details in "Finish protocol" in `.github/copilot-instructions.md`)
1. Log: `python scripts/ai_log.py add --prompt-ref 3-two-approver --action "<one per real thing you did>" --tool-used "<only tools that ran>" --run-tests "mvn -q test"`
2. Commit: `git add -A`, then `git commit -m "feat: require two distinct approvers above 500,000" -m "Why: very large invoices need a second Director, and one person must never count twice"`. Adjust the wording to what you really changed. Skip if only `docs/ai-log/` changed.
3. Tell me the commit hash and message.
