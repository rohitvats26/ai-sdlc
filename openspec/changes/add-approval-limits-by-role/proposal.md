# Proposal

## Why

The invoice app must enforce role-based approval limits before any invoice is finalized. Without a shared policy, approvals can be granted by users who lack authority, duplicate approvers can be counted twice, and rejected attempts can leave state in a partially mutated condition.

## What Changes

- Enforce a single-approver policy for amounts up to and including 50,000, where either a Manager or a Director may approve.
- Restrict amounts above 50,000 and up to 500,000 to Director-only approval.
- Require two distinct approvers for amounts above 500,000, with the second approver required to be a Director.
- Prevent duplicate approvers by treating the same user as the same identity regardless of case or surrounding whitespace.
- Return a clear 403 rejection reason when an approval attempt is not permitted and ensure the invoice remains unchanged.
- Record approval history with who approved, role, and timestamp in order.

## Capabilities

### New Capabilities
- `approval-limits`: Enforces invoice approval authority, duplicate-approver checks, refusal behavior, and approval history for role-based decisions.

### Modified Capabilities
- None.

## Impact

- Domain approval logic and invoice state transitions.
- REST API endpoints that accept approval decisions and map refusal reasons to HTTP 403 responses.
- Demo accounts and role checks for Manager and Director identities.
- Unit tests, boundary checks, and Playwright/UI validation for approval scenarios.
