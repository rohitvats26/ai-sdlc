# Design

## Context

The current app models a draft invoice that can be submitted for approval, but approval authority is not yet role-aware. The repository returns live invoice instances, and the policy must be enforced before any mutation. The approvals feature needs to preserve the existing invoice lifecycle while adding role-scoped authority checks, refusal semantics, and historical tracking.

## Goals / Non-Goals

**Goals:**
- Enforce role-based approval limits for invoice decisions.
- Ensure refusal attempts are rejected before mutation and do not alter invoice state.
- Keep approval history auditable and in the order approvals are accepted.
- Preserve the existing API and UI semantics while adding Manager and Director validation.

**Non-Goals:**
- Changing the overall invoice lifecycle beyond approval authority checks.
- Replacing the in-memory repository or introducing a database.
- Allowing unapproved partial approvals or side-step bypasses through controller logic.

## Decisions

### Decision: Manager is not allowed to be the first approver above 500,000
- Question: May a Manager be the first approver on an invoice above 500,000?
- Options:
  1. Allow the first approver to be a Manager, then require the second to be a Director.
  2. Require both approvers to be Directors above 500,000.
- Chosen option: Require both approvers to be Directors.
- Consequence: This follows the safe reading of the policy and avoids granting authority beyond the Manager limit even before the second approval is considered.

### Decision: Same-user detection ignores case and spaces
- Question: Does the duplicate-approver check treat the same user as identical regardless of spaces or letter case?
- Options:
  1. Compare raw strings exactly.
  2. Normalize by trimming and lowercasing before comparison.
- Chosen option: Normalize by trimming and lowercasing before comparing approver identities.
- Consequence: `Director`, ` director `, and `DIRECTOR` all count as the same user and cannot be used twice.

### Decision: Clean separation of role semantics for existing demo users
- Question: What happens to the existing `Approver` and `Admin` roles and the `demo.approver` account?
- Options:
  1. Reinterpret `Approver` as a Manager or Director.
  2. Keep existing `Approver` and `Admin` roles as distinct, with `Approver` continuing to be a valid low-value approver and `Admin` staying non-authoritative.
- Chosen option: Keep `Approver` and `Admin` distinct; `Approver` remains a low-authority account for the existing demo flow, while `Manager` and `Director` are the explicitly new roles required by the policy.
- Consequence: The invoice policy adds new roles without altering the meaning of existing roles already used by the demo. The `demo.approver` account remains a baseline approver for amounts within its valid scope; the new Manager and Director demo accounts are used for the role-based threshold checks.

### Decision: Refusal validation happens before the first mutation
- Question: When should the system reject a bad approval attempt?
- Options:
  1. Accept the request, mutate invoice state, and only then reject the operation.
  2. Validate the full approval request before any state change, then commit only if valid.
- Chosen option: Validate everything before the first mutation.
- Consequence: The invoice remains unchanged on rejected attempts, satisfying the no-partial-mutation requirement.

## Risks / Trade-offs

- [Risk] Role-specific logic can drift from business expectations unless boundary tests cover 50,000 and 500,000 precisely → Mitigation: add exact decimal boundary tests and a requirement trace table.
- [Risk] Duplicate approver logic can be bypassed by inconsistent identity normalization → Mitigation: normalize by trimming and lowercasing before comparison.
- [Risk] Requirement ambiguity could produce inconsistent UI behavior → Mitigation: keep the safe interpretation and document the assumptions directly in this design and the spec.

## Requirement-to-Test Table

| Requirement | Planned test class | Notes |
| --- | --- | --- |
| Manager and Director limit by amount | `ApprovalServiceTest` | Covers 50,000, 50,000.01, 500,000, and 500,000.01 boundaries |
| Two distinct approver requirement above 500,000 | `ApprovalServiceTest` | Validates duplicate and second-approver enforcement |
| Refused approval leaves invoice unchanged | `ApprovalServiceTest` | Asserts status, amount, decision fields, and history remain untouched |
| API refusal is HTTP 403 with error payload | `InvoiceApiTest` | Checks the external behavior for invalid approval requests |
| UI and Playwright validation | `e2e/tests/*.spec.ts` | Confirms role-based flow and refusal messages in the browser |

## Migration Plan

- Extend role metadata for Manager and Director demo accounts in the app configuration.
- Add role checks in the domain approval policy and service before the invoice mutation.
- Update API error mapping to emit a clear `{ "error": "..." }` message for 403 refusals.
- Verify boundary and no-mutation tests before moving to UI-level validation.

## Open Questions

- No open design question remains after the chosen safe interpretations above; this is a closed design decision for the spec and implementation.
