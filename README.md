# Invoice approval demo (Spring Boot)

A small invoice approval app used for the AI in SDLC assignment. Java 17, Spring Boot 3, in-memory data, plain HTML/JS front end.

## Run

```
mvn spring-boot:run
```
Open http://localhost:5000 and sign in with one of the demo accounts below.

## Demo accounts

All demo accounts use the password `ChangeMe123!`. These are local demo credentials, not real ones. They live in `src/main/resources/application.yml`.

| Username | Role | What it can do | Available |
| --- | --- | --- | --- |
| `demo.approver` | Approver | Approve and reject invoices (no limit, until the limits are added) | Baseline |
| `demo.admin` | Admin | Approve, reject and delete invoices | Baseline |
| `demo.manager` | Manager | Approve invoices up to 50,000 | Added in step 2 (`2-single-approver`) |
| `demo.director` | Director | Approve invoices up to 500,000; give an approval above 500,000 | Added in step 2 (`2-single-approver`) |
| `demo.director2` | Director | Second approver above 500,000 | Added in step 2 (`2-single-approver`) |

Keep this table in step with `application.yml`: if you add, rename or remove an account, update it in the same commit.

## What it does

Create an invoice, submit it for approval, then an approver approves it or rejects it with a reason. Invoices move Draft, Pending Approval, then Approved or Rejected.

## Approval limits by role (the feature)

Built in steps 2 and 3. Amounts use `BigDecimal` and are compared exactly.

| Invoice amount | Who may approve | Approvals needed |
| --- | --- | --- |
| up to and including 50,000 | Manager or Director | 1 |
| above 50,000, up to and including 500,000 | Director only | 1 |
| above 500,000 | first approver must be a Director; second approver must also be a Director and must be different from the first | 2 |

- The same user never counts twice (case and surrounding spaces are ignored).
- A refused attempt returns a clear reason (HTTP 403 with `{ "error": ... }`) and changes nothing on the invoice.
- The first approval above 500,000 keeps the invoice pending and records the approval; the second valid Director finalizes it.
- The invoices table shows approvals recorded out of required, for example `1 of 2`.

Before the feature is built, the app still approves any invoice for any Approver or Admin.

## Tests

```
mvn test                                   # unit and API tests
cd e2e && npm install && npx playwright install chromium && npm test   # end-to-end (starts the app itself)
mvn test-compile org.pitest:pitest-maven:mutationCoverage              # mutation testing (PIT), report in target/pit-reports
```

**End-to-end tests open a real browser window** and run slowly on purpose (`headless: false`, `slowMo: 1000`, one second per action), so you can watch and record them. They need a desktop session. To run one test only, use `npx playwright test -g "<part of the test title>"`. For a faster, invisible run (for example on a build server), temporarily set `headless: true` and remove `slowMo` in `e2e/playwright.config.ts`.

## Layout

```
src/main/java/com/example/invoiceapp/domain   business rules (no Spring)
src/main/java/com/example/invoiceapp/api      controllers, security, error mapping
src/main/java/com/example/invoiceapp/infra    in-memory repository
src/main/resources/static                     web UI
src/test/java                                 JUnit 5 tests
e2e/                                          Playwright tests
openspec/                                     spec-driven change (created in step 1)
AGENTS.md                                     conventions for AI coding agents
docs/                                         use cases, AI log, review findings, Copilot runbook
```

## Working on the approval-limits feature

See [AGENTS.md](AGENTS.md) for the rules and [docs/copilot-runbook.md](docs/copilot-runbook.md) for the workflow with GitHub Copilot. AI usage is logged per prompt in `docs/ai-log/ai-log.jsonl` (readable summary: `docs/ai-interaction-log.md`).
