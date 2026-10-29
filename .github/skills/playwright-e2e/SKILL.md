---
name: playwright-e2e
description: How to write the Playwright end-to-end tests for this app (page objects, role-based locators, self-contained data, refusal test plus control). Use when adding or fixing anything in the e2e folder or the web UI the tests depend on.
---

# Playwright end-to-end tests

## Structure
- Page objects in `e2e/pages/` (login, invoices, approvals). Tests in `e2e/tests/` read like a story.
- Locate with `getByRole`, `getByLabel`, `getByText` scoped to a row or list item. Never CSS, XPath or nth-child.
- Every test creates its own invoice with a unique customer name (`E2E <label> <timestamp>`). Never depend on seed data or test order.

## The three tests
1. **Refusal (required).** Title contains the word `refused`. A Manager tries 50,000.01. Check: the reason text is shown, status still "Pending Approval", amount "$50,000.01", approvals "0 of 1".
2. **Control.** A Director approves the same amount. This proves the page works, so test 1 cannot pass because of a broken page.
3. **Two approvers.** 600,000: first Director approves ("1 of 2"), the same Director again is refused, a second Director completes it ("2 of 2").

## Config rules
`e2e/playwright.config.ts` uses `headless: false` and `slowMo: 1000` on purpose (visible, recordable). Do not add `waitForTimeout`; rely on auto-waiting and `expect(...).toBeVisible()`. One test only: `npx playwright test -g "refused"`.

## UI contract the tests rely on
Keep element ids and accessible names stable: the Approvals column ("recorded of required"), the alert that shows the refusal reason, the Approve and Submit buttons named by invoice id.

## When a test fails
Read the error and the trace first (`npx playwright show-report`). Fix the locator or the UI. Never weaken an assertion to get green.
