---
applyTo: "src/test/java/**/*.java,e2e/**/*.ts"
---
JUnit 5 + AssertJ: `@ParameterizedTest` with `@CsvSource` and string amounts converted with `new BigDecimal(...)`. Refusal tests take a snapshot of the invoice before the attempt and prove status, amount, decision fields and approvals are unchanged, and assert the key fact in the message with `assertThat(message).contains(...)`.
Playwright: page objects in `e2e/pages`, role-based locators only, each test creates its own invoice with a unique customer name, include a control test for an allowed role.
