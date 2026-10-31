# Approval limits specification

## ADDED Requirements

### Requirement: Manager and Director limits are enforced by invoice amount
The system SHALL allow a single Manager or Director to approve invoices at 50,000 or less, SHALL require a Director for invoices above 50,000 and up to 500,000, and SHALL require two distinct approvers for invoices above 500,000, with the second approver being a Director.

#### Scenario: Manager approves a 50,000 invoice
- Given an invoice amount of 50,000.00
- When a Manager approves the invoice
- Then the approval SHALL be accepted and the invoice SHALL move to the approved state.

#### Scenario: Director approves a 500,000 invoice
- Given an invoice amount of 500,000.00
- When a Director approves the invoice
- Then the approval SHALL be accepted and the invoice SHALL move to the approved state.

#### Scenario: Manager is denied above 50,000
- Given an invoice amount of 50,000.01
- When a Manager attempts to approve the invoice
- Then the system SHALL reject the approval and SHALL return a clear reason that the role is not allowed for that amount.

### Requirement: Two approvers are required above 500,000
The system SHALL require two distinct users to approve invoices above 500,000, and the second approver SHALL be a Director.

#### Scenario: Two Directors approve a 500,000.01 invoice
- Given an invoice amount of 500,000.01
- When two distinct Directors approve the invoice in sequence
- Then the invoice SHALL be approved only after the second Director authorizes it.

#### Scenario: A Manager cannot be the first approver above 500,000
- Given an invoice amount above 500,000
- When a Manager attempts to serve as the first approver
- Then the system SHALL reject the approval because the first approver is not authorized at that threshold.

#### Scenario: A non-Director cannot be the second approver above 500,000
- Given an invoice amount above 500,000
- When a Director is the first approver but a Manager or Approver is the second approver
- Then the system SHALL reject the second approval because the second approver must be a Director.

### Requirement: Duplicate approvers are rejected
The system SHALL never count the same person as both approvers, and same-user checks SHALL ignore case and surrounding whitespace differences in the approver identity.

#### Scenario: Same user is denied twice
- Given an invoice above 500,000 and a valid first approver
- When the same user attempts to approve again with different letter case or added spaces
- Then the system SHALL reject the second approval as a duplicate approver.

#### Scenario: Distinct names are accepted
- Given two approvers whose identities differ after trimming and normalizing case
- When each one approves in turn under the valid approval policy
- Then both approvals SHALL count as distinct approvers.

### Requirement: Refused approvals leave the invoice unchanged
The system SHALL validate the proposed approval before the first mutation and SHALL reject invalid attempts without changing the invoice status, amount, decision fields, or approval history.

#### Scenario: Rejected approval does not mutate invoice state
- Given an invoice in a valid state with a stored status, amount, and approval history
- When an approval is refused because the user is unauthorized or the approver is duplicated
- Then the system SHALL return a clear error reason and SHALL leave status, amount, decision fields, and approval history exactly unchanged.

### Requirement: Invalid approval input is rejected clearly
The system SHALL reject blank approver values, unknown roles, and invalid amounts before updating any invoice state.

#### Scenario: Blank approver is rejected
- Given a request to approve an invoice with a blank approver identifier
- When validation runs
- Then the system SHALL reject the request with a clear error.

#### Scenario: Unknown role is rejected
- Given a role value that does not map to a supported approval role
- When the approval is evaluated
- Then the system SHALL reject the request and record the reason.

### Requirement: Approval history is recorded in order
The system SHALL retain approval history entries containing the user, role, and timestamp in consistent order for auditing and UI display.

#### Scenario: Approval history is stored in order
- Given an approval flow with multiple valid approvers
- When each approval is recorded
- Then the system SHALL keep each entry with who approved, their role, and when the decision occurred, in the sequence the approvals were accepted.

### Requirement: Boundary values are tested exactly
The system SHALL use exact decimal comparisons and SHALL cover the defined thresholds at 50,000, 50,000.01, 500,000, and 500,000.01.

#### Scenario: Threshold boundaries are evaluated correctly
- Given an invoice amount equal to 50,000.00, 50,000.01, 500,000.00, and 500,000.01
- When the approval policy evaluates those amounts
- Then the system SHALL apply the correct role and count rules for each threshold boundary without off-by-one behavior.
