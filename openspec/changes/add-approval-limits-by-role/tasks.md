# Tasks

## 1. Approval policy and refusal semantics

- [ ] 1.1 Define the approval policy and boundary rules for 50,000, 50,000.01, 500,000, and 500,000.01, and verify the requirements match the approved spec.
- [ ] 1.2 Implement the no-mutation refusal behavior so invalid approvals return a clear reason without changing status, amount, decision fields, or approval history, and verify with unit tests.
- [ ] 1.3 Add duplicate-approver normalization and validation so identity comparison ignores case and spaces, and verify the negative test fails when the same approver is reused.

## 2. Two-approver and role checks

- [ ] 2.1 Enforce the Director-only rule for invoices above 50,000 and up to 500,000, and verify the valid/invalid cases with unit tests.
- [ ] 2.2 Enforce the two-distinct-approver requirement above 500,000, including the second-approver Director check, and verify the valid and rejected scenarios.
- [ ] 2.3 Record approval history in order with user, role, and timestamp, and verify the audit trail is preserved in the invoice data.

## 3. API and UI behavior

- [ ] 3.1 Update API-level validation and error mapping for 403 refusals, and verify the endpoint returns the expected `{ "error": "..." }` payload.
- [ ] 3.2 Add or update UI behavior to show role-aware approval options and refusal messaging, and verify the browser flow matches the expected approval rules.
- [ ] 3.3 Add Playwright coverage for valid approval and refusal flows, and verify the E2E suite passes for the targeted approval scenarios.

## 4. Verification and review

- [ ] 4.1 Run the focused unit and API tests for the approval policy, and verify the suite passes before implementation review.
- [ ] 4.2 Run mutation testing for the approval logic and verify the surviving mutation count is explained and addressed by stronger assertions.
- [ ] 4.3 Review the final diff against the spec and verify the findings document is recorded before archive or PR submission.
