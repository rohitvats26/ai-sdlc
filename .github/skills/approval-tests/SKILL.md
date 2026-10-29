---
name: approval-tests
description: How to write unit and concurrency tests for the approval rules so they would catch a real mistake, and how to turn surviving PIT mutants into tests. Use when writing, reviewing or strengthening JUnit tests for ApprovalPolicy or ApprovalService.
---

# Approval tests

## Every refusal test has four parts
1. Take a snapshot of the invoice first: status, amount, `decidedBy`, `decidedAt`, number of approvals.
2. Attempt the approval and assert the exact exception type.
3. Assert the key fact in the message (`assertThat(message).contains("50,000")`, the role, the invoice id), not the whole sentence.
4. Compare the invoice with the snapshot: nothing changed.

```java
record Snapshot(InvoiceStatus status, BigDecimal amount, String decidedBy, Instant decidedAt, int approvals) {
    static Snapshot of(Invoice i) { return new Snapshot(i.getStatus(), i.getAmount(), i.getDecidedBy(), i.getDecidedAt(), i.getApprovals().size()); }
}
```
(Adapt the getters to the real classes. A test that only checks "an exception was thrown" is a weak test.)

## Boundaries (one parameterized test per rule)
Use `@ParameterizedTest` with `@CsvSource` and `new BigDecimal(text)`: 50000, 50000.01, 500000, 500000.01, and one value well inside each band. Include a Manager and a Director in each band.

## Success tests check more than the status
Assert status, `decidedBy`, `decidedAt` not null, the approval history contents and order, and `approvals required` versus `recorded`.

## Concurrency test (must fail without the lock)
Two or more threads approve the same invoice. Widen the gap between "check" and "write" so a missing lock fails reliably: inject a clock or wrap the repository so it sleeps about 10 ms after the check. Assert exactly one approval per user. Prove it: remove the lock, see the test fail, put the lock back.

## Survived mutants, what to add
| Mutant that survived | Test to add |
| --- | --- |
| `>` changed to `>=` or limit changed by 1 | boundary at the exact limit and one cent above |
| same-user check case-sensitive or untrimmed | `Demo.Director` / `  demo.director ` |
| status or `decidedBy` not set | success test asserting those fields |
| refusal side effect | snapshot comparison |
| role check removed | Manager refused where only a Director may approve |
| message changed | `contains` on limit, amount, role |
Equivalent mutants (cannot change behaviour): say so and skip; do not chase 100 percent.
