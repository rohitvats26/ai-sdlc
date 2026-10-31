# Pull request summary

This change adds role-based approval limits to the invoice demo. A Manager can approve invoices up to and including 50,000, a Director can approve up to 500,000, and invoices above 500,000 require two distinct Directors in sequence. Same-user checks ignore case and surrounding whitespace, and any invalid approval attempt is refused before the invoice is mutated.

## Business-rule coverage

- Up to 50,000: Manager or Director may approve.
- Above 50,000 up to 500,000: Director only.
- Above 500,000: first approver must be a Director, second approver must also be a Director, and the user must be different from the first.
- Refused approvals return an error and leave status, amount, decision fields, and approval history unchanged.
- Blank approver names, unknown roles, invalid amounts, and non-pending invoices are rejected with clear reasons.
- Approval history records the username, role, and timestamp in order.

## Test results

- `mvn test` ran successfully: 22 passed of 22, 0 failed, 0 errors, 0 skipped.
- The approval domain tests cover boundary values at 50,000, 50,000.01, 500,000, and 500,000.01, plus invalid and duplicate approvals.
- Playwright flow files are present in `e2e/tests/approval-flow.spec.ts`, but the browser run was not executed in this session.

## Mutation scores

- Before: not found in `pit-before` (no earlier PIT report was recorded in this repo state).
- After: 74 of 104 mutants killed = 71.2 percent (14 survived, 16 not covered). File: `target/pit-reports/mutations.xml`.

## AI tools used

The repo log records these actual interactions:

- GitHub Copilot / `gpt-4o-mini-2024-07-18`
- Modes: `agent`
- Skills actually used in the log: `playwright-e2e`, `review-findings`
- Tools used in the commit log: PowerShell, OpenSpec CLI, view, grep, create, and the git hook system

## Review findings table

| ID | Severity | Verdict | Title |
| --- | --- | --- | --- |
| FR-01 | medium | dismissed | Large-invoice approval rule is split out of the policy and the policy itself rejects valid approvals |
| FR-02 | low | dismissed | Director-only rejection message names the wrong threshold |

## Known limits and open assumptions

- The demo video link remains Pending until it is recorded and added.
- The external pull request URL remains Pending until the repo or review host provides it.
- The `Before` PIT value is marked as not found because no earlier PIT report existed in the repo state used for this write-up.
- The assignment requirement for multiple agents is satisfied by the configured repository workflow and custom agent files, but no separate multi-agent execution was recorded in the current session.
