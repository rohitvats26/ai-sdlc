---
applyTo: "src/main/java/**/*.java"
---
Follow the rules table in AGENTS.md. Keep decisions in a pure policy class and state changes in `ApprovalService`, after the policy accepts. Compare amounts with `BigDecimal.compareTo`. Same-user checks trim and ignore case. The `domain` package has no Spring imports; wire beans in `api/AppConfig`. Do not edit tests in the same step.
