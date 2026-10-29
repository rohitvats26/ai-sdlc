---
description: Step 5. Show approval progress in the UI and add the Playwright tests.
mode: agent
---
Goal: make approvals visible in the UI and prove a refused approval through the browser.

## Before you start (stop and tell me if a check fails)
Steps 2 to 4 are committed, `mvn test` is green, and `cd e2e && npm install && npx playwright install chromium` has been run.

## Read only these
`src/main/resources/static/*`, `e2e/playwright.config.ts`, `e2e/package.json`, `AGENTS.md`.

## Skills (open the file if your Copilot does not load it for you)
- `playwright-e2e` (`.github/skills/playwright-e2e/SKILL.md`): page objects, locators, the three tests

## Plan first (in the chat)
The UI changes, and the title and steps of the three tests.

## UI (`src/main/resources/static`)
Add an "Approvals" column to the invoices table ("recorded of required", for example "1 of 2"); show who approved so far in the pending list; show the refusal reason in the existing alert (if a 403 has no message, show "You do not have permission to do that."). Keep existing element ids and accessible names.

## Playwright (`e2e/`)
Follow skill `playwright-e2e` (page objects, role-based locators, each test creates its own invoice).
- Test 1 (required): the title must contain the word **refused**. A Manager tries 50,000.01. Check the reason text, status still "Pending Approval", amount "$50,000.01", approvals "0 of 1".
- Test 2 (control): a Director approves the same amount.
- Test 3: a 600,000 invoice needs two different Directors; the same Director twice is refused; the second completes it.

## Rules
Keep `e2e/playwright.config.ts` as it is (`headless: false`, `slowMo: 1000`): the run is slow on purpose, wait for it. Do not change the API or domain. If a test still fails after 3 attempts, stop and tell me; do not weaken an assertion.

## Done when
`cd e2e && npx playwright test -g "refused"` passes, then `npm test` passes (show both), and `mvn test` still passes. Reply: files changed, results.

## Finish (in this order; details in "Finish protocol" in `.github/copilot-instructions.md`)
1. Log: `python scripts/ai_log.py add --prompt-ref 5-e2e-ui --action "<one per real thing you did>" --tool-used "<only tools that ran>" --command-run "npm --prefix e2e test"`
2. Commit: `git add -A`, then `git commit -m "feat: show approval progress and add Playwright tests" -m "Why: users must see the refusal reason and approvals so far, and the browser test proves it"`. Adjust the wording to what you really changed. Skip if only `docs/ai-log/` changed.
3. Tell me the commit hash and message.
