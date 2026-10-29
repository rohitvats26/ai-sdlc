---
name: approval-rules
description: Rules and common traps for invoice approval limits by role in this repo (Manager up to 50,000, Director up to 500,000, two distinct Directors above 500,000, refused attempts change nothing). Use when writing the spec, designing or changing approval logic, or checking a refusal.
---

# Approval rules

## The contract
| Invoice amount | Who may approve | Approvals needed |
| --- | --- | --- |
| up to and including 50,000 | Manager or Director | 1 |
| above 50,000, up to and including 500,000 | Director | 1 |
| above 500,000 | two different users; the second must be a Director (default decision: both Directors) | 2 |

A refused attempt returns a clear reason (HTTP 403 `{ "error": ... }`) and changes nothing: status, amount, `decidedBy`, `decidedAt`, approval history.

## Design that works
- A pure policy class decides (never changes the invoice). `ApprovalService` calls it first and changes the invoice only after it accepts.
- Read, check and write happen under one lock, so two requests cannot both pass the checks.
- Build the approver from the session (`username`, `role`); never from the request body.
- Compare amounts with `BigDecimal.compareTo` against `new BigDecimal("50000")` and `new BigDecimal("500000")`.
- The refusal message names: the limit, the amount, the invoice id, and who is needed.

## Traps (check each one)
1. Changing status or adding an approval record before the policy has accepted.
2. `equals` on `BigDecimal` (50000.0 is not equal to 50000.00); or `double`.
3. `>=` instead of `>` at 50,000 or 500,000 (50,000 is allowed for a Manager, 50,000.01 is not).
4. Same-user check that is case-sensitive or does not trim (`Demo.Director` and `demo.director` are one person).
5. Counting the first approval as a full approval; or setting `decidedBy` after only the first of two.
6. The role check applied only to the second approver (decide the first-approver rule in `design.md` and test it).
7. Unknown role or blank name accepted; an invoice that is not pending accepted.
8. A lock that the tests never prove is needed.

## Where things live
`src/main/java/com/example/invoiceapp/domain` (rules, no Spring), `.../api` (controllers, error mapping), `src/main/resources/application.yml` (demo accounts, keep README in step).
