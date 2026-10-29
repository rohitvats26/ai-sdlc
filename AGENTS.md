# Project conventions for AI agents

Invoice approval demo app: Spring Boot 3 (Java 17) REST API with a small static web UI. In-memory store, no database. Read by GitHub Copilot (agent mode, coding agent) and any other agent.

## Layout (base package `com.example.invoiceapp`)

- `domain/`: business rules, **no Spring imports**. Today: `ApprovalService`, `Invoice`, `InvoiceStatus`, `InvoiceRepository`, `InvoiceNotFoundException`, `InvalidInvoiceStateException`.
- `api/`: controllers, `ApiExceptionHandler` (error mapping), `AppConfig` (wires domain beans, registers the role check), `api/security/` (sign-in session, `@RequireRole`).
- `infra/`: `InMemoryInvoiceRepository` (seeded demo data).
- `src/main/resources/static/`: web UI (`index.html`, `app.js`, `styles.css`). Keep element ids and accessible names stable; e2e tests depend on them.
- `src/test/java/`: JUnit 5 tests, mirroring the main packages, named `<ClassUnderTest>Test`.
- `e2e/`: Playwright tests (`tests/`) and page objects (`pages/`).
- `openspec/`: spec-driven artifacts. The change for this work is `add-approval-limits-by-role` (create it first, see `docs/copilot-runbook.md`).
- `docs/`: use cases, AI interaction log, review findings.

## Feature being built: approval limits by role

Amounts are `BigDecimal`, compared with `compareTo`, never `double`/`float` and never `equals` (scale differs: 50000.0 vs 50000.00).

| Invoice amount | Who may approve | Approvals needed |
| --- | --- | --- |
| up to and including 50,000 | Manager or Director | 1 |
| above 50,000, up to and including 500,000 | Director only | 1 |
| above 500,000 | two distinct users; the second must be a Director | 2 |

- The same user never counts as both approvers. Decide whether "same user" ignores case and spaces (it should) and write that into the spec.
- A refused attempt returns a clear reason and changes nothing about the invoice: status, amount, decision fields and approval history stay as they were. Validate everything before the first mutation.
- Open question to settle in the spec and record as an assumption: may a Manager be the first approver above 500,000? A Manager has no authority above 50,000, so the safe reading is that both approvers must be Directors.
- Do not weaken a rule to make a test pass. If a rule seems wrong, stop and report it.

Suggested shape (create these in `domain/`): `ApprovalPolicy` (static, pure: decides), `ApprovalService` (applies: validate, then mutate), `Approver` + `ApproverRole` (MANAGER, DIRECTOR), `ApprovalRecord` (who, role, when), `ApprovalRejectedException` (mapped to HTTP 403 with an `error` body in `ApiExceptionHandler`).

## Layering

- Business rules live in `domain/`. Never in controllers or config classes.
- Controllers are thin: read the session, call the service, return the result. Errors are mapped centrally in `ApiExceptionHandler` to `{ "error": message }` (404 not found, 409 wrong state, 400 bad input).
- Every `/api` endpoint except `/api/auth/login` needs a bearer token (`SessionAuthFilter`). Restrict by role with `@RequireRole`.
- The in-memory repository returns live instances, so never mutate an invoice before the decision is final. Take one lock around read, validate and write.
- JSON: `InvoiceStatus` is written as `Draft`, `PendingApproval`, `Approved`, `Rejected` (the UI relies on it).

## Commands

- Build and unit tests: `mvn test` (full: `mvn verify`)
- Run the app: `mvn spring-boot:run`, then http://localhost:5000
- E2E: `cd e2e && npm install && npx playwright install chromium && npm test` (starts the app itself; opens a visible browser with `slowMo: 1000` by design, so it needs a desktop; one test: `npx playwright test -g "<title part>"`)
- Mutation testing (PIT): `mvn test-compile org.pitest:pitest-maven:mutationCoverage`, report in `target/pit-reports/`
- All the numbers for the write-up and demo: `python scripts/evidence.py` (reads git, Maven, PIT, findings and the AI log; add `--write` to save `docs/evidence.md`)
- Lint the step prompts: `python scripts/check_prompts.py` (the pre-commit hook runs it when `.github/prompts/` changes)
- Validate review findings: `python3 scripts/hooks/validate-findings.py --final docs/review/findings.json`
- Validate spec: `openspec validate add-approval-limits-by-role --strict`

## Testing expectations

- Every rule needs a positive and a negative test. Every refusal test must also assert the invoice is unchanged (status, amount, approvals), not only that an exception was thrown.
- Test each boundary: 50,000 / 50,000.01 / 500,000 / 500,000.01, using `new BigDecimal("...")` from strings.
- E2E uses page objects and role-based locators, never CSS or XPath. Each test creates its own invoice.
- Run PIT after changing the approval code; a surviving mutant means a missing assertion.

## Review expectations

Before a PR, review the diff in a fresh chat with prompt `6-review-pr`. Findings go in `docs/review/findings.json` (checked by `validate-findings.py`). Every finding gets exactly one verdict: `fixed`, `dismissed` (with reason) or `deferred` (with reason). Treat findings as leads to verify. Check: rules vs spec, partial change on refusal, money types, authorisation, thread safety, test strength, secrets.

## Agent workflow rules

- Read the spec first. Inspect existing code before editing. No unrelated changes.
- One small step per commit, with a message saying what changed and why (`-m "<type>: <what>" -m "Why: <reason>"`). A step prompt commits its own work after logging it. Never push, amend or rewrite history.
- Do not bypass tests or the commit guard (`git config core.hooksPath .githooks`). Do not claim a command ran if it did not.
- Log every prompt right after it finishes, one entry per prompt, in `docs/ai-log/ai-log.jsonl` with `scripts/ai_log.py add` (guide: `docs/ai-log/SCHEMA.md`). Real tool, mode, prompts, what ran (the model is detected automatically from the Copilot Chat log; never type or guess it); the human then adds their review with `annotate last`. The pre-commit hook blocks a commit with no new log entry. Report assumptions and open issues.
- Skills (short how-to guides) live in `.github/skills/`: `approval-rules`, `approval-tests`, `playwright-e2e`, `review-findings`, `ai-log`, plus `openspec-propose` from OpenSpec. Use them, and list a skill in the AI log only when it really ran.
- Role agents live in `.github/agents/`; step prompts in `.github/prompts/` (each has preconditions, a plan-first step and a "Done when" list, then follows the Finish protocol in `.github/copilot-instructions.md`: log, then commit). Keep step prompts under 50 lines and run the linter after editing one. Give each disjoint files.

## Demo accounts (not real credentials)

Configured in `src/main/resources/application.yml`. Baseline has `demo.approver` (Approver) and `demo.admin` (Admin). This work should add `demo.manager` (Manager), `demo.director` and `demo.director2` (Director). Password for all: `ChangeMe123!`.

## Never

- Commit real credentials, tokens or customer data.
- Put business logic in controllers or config.
- Use `double` or `float` for money.
