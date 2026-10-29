---
description: Step 2. Manager and Director limits only (task group 1).
mode: agent
---
Goal: task group 1 of the spec only. No two-approver logic yet.

## Before you start (stop and tell me if a check fails)
Step 1 is committed (`openspec validate add-approval-limits-by-role --strict` passes) and `mvn test` is green now.

## Read only these
The spec, design and tasks in `openspec/changes/add-approval-limits-by-role/`, `AGENTS.md`, `src/main/java/**`, `src/test/java/**`.

## Skills (open the file if your Copilot does not load it for you)
- `approval-rules` (`.github/skills/approval-rules/SKILL.md`): rules, design and traps
- `approval-tests` (`.github/skills/approval-tests/SKILL.md`): refusal test recipe and boundaries

## Plan first (in the chat)
The classes you will add or change, and every test case (name and what it proves).

## Build
- Domain types: approver, role (Manager, Director), approval record (who, role, when), a "rejected" exception carrying a clear reason.
- A pure policy class that decides if an approver may approve and never changes the invoice. `ApprovalService` calls it first and changes the invoice only after it accepts.
- Manager up to 50,000, Director up to 500,000; anything above 500,000 is refused for everyone in this step. The refusal message names the limit, the amount and the invoice id; map it to HTTP 403 with `{ "error": reason }`.
- Add `demo.manager`, `demo.director`, `demo.director2` to `application.yml`; let Manager and Director call the approval endpoints.
- Update `README.md` now: the demo accounts table must match `application.yml`; add a short "Approval limits" section.

## Tests
Follow skill `approval-tests`. Cover: the four boundaries (50,000 / 50,000.01 / 500,000 / 500,000.01), blank approver, unknown role, invalid amount, invoice not pending. Every refusal test snapshots the invoice and proves nothing changed.

## Rules
`BigDecimal` with `compareTo`; no Spring in `domain`; update old tests to new signatures but never weaken or delete one; touch only what you need. If a test still fails after 3 attempts, stop and tell me; never change a rule or test to make it pass.

## Done when
`mvn test` passes; your reply has a table (spec requirement of group 1 to the test that proves it); no `TODO` or commented-out code. Do NOT build the two-approver rule, change the UI or edit the spec.

## Finish (in this order; details in "Finish protocol" in `.github/copilot-instructions.md`)
1. Log: `python scripts/ai_log.py add --prompt-ref 2-single-approver --action "<one per real thing you did>" --tool-used "<only tools that ran>" --run-tests "mvn -q test"`
2. Commit: `git add -A`, then `git commit -m "feat: enforce manager and director limits" -m "Why: approval authority must depend on the approver's role"`. Adjust the wording to what you really changed. Skip if only `docs/ai-log/` changed.
3. Tell me the commit hash and message.
