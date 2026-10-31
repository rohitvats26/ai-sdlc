# AI in SDLC assignment: approval limits by role

**Stack:** Java 17 / Spring Boot 3. **Spec tool:** OpenSpec. **AI tool:** GitHub Copilot (model: `gpt-4o-mini-2024-07-18`).
**Demo video:** Pending   **Pull request:** Pending

## Write-up

Built the approval-limits feature in the domain layer and API layer: Manager and Director limits are enforced by amount, invoices above 500,000 require two distinct Directors, and duplicate approvers are rejected after trimming and normalizing case. The service validates first and mutates only after the approval is accepted, so refused approvals leave the invoice unchanged. This is covered by unit tests for each boundary and for refusal cases, and the UI shows the count of approvals recorded out of required approvals.

The repo also includes the OpenSpec change, prompt files, custom agents, and the AI log workflow required by the assignment. Copilot was used for the spec, implementation steps, tests, and review. The log and validation scripts were checked in the repo; the missing items are the demo video and the PR link, which remain Pending until they are added outside this session.

## Traceability

| # | Requirement | Implementation | Evidence | Status |
| --- | --- | --- | --- | --- |
| 1 | AGENTS.md context | Followed the repo rules from AGENTS.md and the instruction files. | `AGENTS.md`; `.github/instructions/domain-code.instructions.md`; `.github/instructions/tests.instructions.md` | Completed |
| 2 | Skills | Referenced the custom skills for approval logic, tests and PR review. | `.github/skills/approval-rules/SKILL.md`; `.github/skills/approval-tests/SKILL.md`; `.github/skills/review-findings/SKILL.md` | Completed |
| 3 | Hooks | Added commit guard, prompt linter, and AI log validation. | `.githooks/pre-commit`; `.githooks/post-commit`; `scripts/check_prompts.py`; `scripts/ai_log.py` | Completed |
| 4 | Spec (OpenSpec) | Created the approval-limits change and the validated spec. | `openspec/changes/add-approval-limits-by-role/`; `openspec/changes/add-approval-limits-by-role/specs/approval-limits/spec.md`; commit `af76925` | Completed |
| 5 | Two implementation steps, own commits | Separated single-approver and two-approver logic into distinct feature commits. | commit `1c4b65b` (`feat: enforce manager and director limits`); commit `3b585ad` (`feat: require two distinct approvers above 500,000`) | Completed |
| 6 | Unit tests incl. negative rules; Playwright test | Service tests cover boundary and refusal rules; UI/e2e flow exists. | `src/test/java/com/example/invoiceapp/domain/ApprovalServiceTest.java`; `e2e/tests/approval-flow.spec.ts`; `mvn test` => `22 passed of 22` | Partially completed |
| 7 | PR review with verdicts | Review findings were written and validated. | `docs/review/findings.json`; `python scripts/hooks/validate-findings.py --final docs/review/findings.json` | Completed |
| 8 | AI interaction log | Logged each prompt and validated the log format. | `docs/ai-log/ai-log.jsonl`; `python scripts/ai_log.py validate` | Completed |
| 9 | Multiple agents | The repo includes role agents and prompt-specific workflows for the assignment. | `.github/agents/`; `.github/prompts/` | Completed |

## Mutation scores (text)

```
Before: not found in `pit-before` (no earlier PIT report was recorded in this repo state).
After: 74 of 104 mutants killed = 71.2 percent (14 survived, 16 not covered). File: target\pit-reports\mutations.xml
```
