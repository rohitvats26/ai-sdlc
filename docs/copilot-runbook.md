# Building this feature with GitHub Copilot (Java)

The feature is still to be built by you with Copilot. This repo has the baseline Spring Boot app plus Copilot configuration: `AGENTS.md`, `.github/copilot-instructions.md`, `.github/instructions/`, seven numbered step prompts in `.github/prompts/`, role agents in `.github/agents/`, OpenSpec skills in `.github/skills/`, a commit guard, and a log script with structured JSONL output. The free Copilot tier is enough. Prompt files and custom agents need VS Code with Copilot Chat; features vary by plan and version, so use what your account shows.

## Setup (once)

1. Install JDK 17 and Maven 3.9+. Fork the repo, clone it, open in VS Code, sign in to GitHub Copilot and Copilot Chat.
2. **First run `mvn test`.** The baseline was written without access to Maven Central, so it was compile-checked only for the framework-free domain classes. If anything in `api/` fails to compile or a test fails, fix that first (ask Copilot, review the change, commit as `fix: ...`) and keep it as your baseline.
3. `git config core.hooksPath .githooks` (blocks a commit while tests fail or `findings.json` is invalid).
4. `npm i -g @fission-ai/openspec`; `cd e2e && npm install && npx playwright install chromium`.
5. `mvn spring-boot:run`, open http://localhost:5000, sign in as `demo.approver` / `ChangeMe123!` and click through once.

## Steps (Chat in Agent mode; each prompt logs itself, then commits its own work)

| Step | Prompt | You check | Commit message idea |
| --- | --- | --- | --- |
| 1 Spec | `1-spec` | the baseline `mvn test` result is reported first; `openspec validate ... --strict` passes; ambiguities written down as assumptions | `docs: spec for approval limits by role` |
| 2 Limits | `2-single-approver` | `mvn test` green; a refused attempt leaves the invoice unchanged | `feat: enforce manager and director limits` |
| 3 Two approvers | `3-two-approver` | same user never counts twice; second approver is a Director | `feat: require two distinct approvers above 500,000` |
| 4 Tests | `4-strengthen-tests` | PIT score before and after pasted as text; `pit-before` folder saved | `test: strengthen approval tests` |
| 5 UI + e2e | `5-e2e-ui` | `cd e2e && npm test` passes | `feat: show approval progress; test: e2e refusal` |
| 6 Review | `6-review-pr` in a **fresh chat** | every finding gets fixed / dismissed / deferred plus a reason; `validate-findings.py --final` | `docs: review findings` |
| 7 Write-up | `7-write-up` | every claim has evidence; pending items marked Pending | `docs: assignment write-up` |

Every step prompt checks its preconditions first (previous step committed, tests green), states a plan, works to a "Done when" list, stops after 3 failed attempts instead of weakening a test, then logs and commits. If you edit a prompt, run `python scripts/check_prompts.py`. The shared log-and-commit rules live in `.github/copilot-instructions.md` ("Finish protocol"), which Copilot attaches to every chat; each prompt only holds the exact commands. Before the write-up, run `python scripts/evidence.py`: it prints every number you need (commits, test counts, mutation scores, findings, log summary).

Ask of every generated test: would this fail if the rule were wrong? PIT answers that. (The assignment's Stryker note is for .NET; PIT is the Java equivalent.)

## Logging (required): one entry per prompt, right after it finishes

Full guide: `docs/ai-log/SCHEMA.md`. The log is `docs/ai-log/ai-log.jsonl`, with a readable summary in `docs/ai-interaction-log.md`.

Once, before the first prompt:
```
python scripts/ai_log.py config --tool "GitHub Copilot" --mode agent
python scripts/ai_log.py detect-model
```
The second command checks that the model Copilot Chat is using can be read automatically. The model is never typed: it is detected from the Copilot Chat log for every entry, so it follows the model picker when you switch. If detection finds nothing on your machine, set `$env:AI_LOG_MODEL = "<name shown in the model picker>"` for the session.

For every prompt:
1. Run the step prompt. When the work is done, its last instructions make Copilot (a) write the log entry for that prompt (prompt text, actions, tools, changed files and test results), then (b) commit the work with a "what" and "why" message. The pre-commit hook runs the tests and checks the log first.
2. Send follow-up prompts if you need them. Copilot logs each one right after it finishes, and commits if files changed.
3. Read what Copilot did: `git show --stat`, `git show`. This is your review.
4. Add your own part now: `python scripts/ai_log.py annotate last --human-correction "..." --human-decision "..." --validation "mvn test green" --outcome successful`. This changes the log file, so it goes into the next step's commit automatically. After the very last step, commit it yourself: `git add -A; git commit -m "docs: add review notes to the AI log" -m "Why: record human review of the last step."`.
5. Something wrong in a commit? Fix it with a new prompt or a new commit. Do not rewrite history after pushing.

If a prompt was missed (you typed one by hand, or the log step was skipped), log it yourself without using Copilot: `python scripts/ai_log.py add --prompt "<paste your exact words>" --stage <spec|implement|test|e2e|review|docs> --action "<what happened>"`, or export the chat and run `python scripts/ai_log.py import-chat chat.json --stage <stage>`. Always record what you did: what you changed, rejected or corrected, and how you checked it. Log failures and rework too. Never log work Copilot did not do.

## Agents, skills, hooks

- **Skills** (`.github/skills/<name>/SKILL.md`): `approval-rules` (rules, design, traps), `approval-tests` (refusal and concurrency test recipes, mutant to test cheat sheet), `playwright-e2e`, `review-findings`, `ai-log`, and `openspec-propose` (from OpenSpec). Each step prompt names the skills it needs and their file path. Newer VS Code versions load skills by their description (this may be a setting such as `chat.useAgentSkills`, depending on your version); if yours does not, the prompt tells Copilot to open the file, so they still work as reference guides. Log a skill with `--skill` only when it really ran.
- **Agents**: pick from `.github/agents/` in the Chat agent picker, or use separate chats per role. Each lists its skills. Record which you used.
- **Hooks**: the commit guard is a plain git hook (tests, prompt linter, log check). If your Copilot setup has its own hook support, use it for test-after-edit; if not, say so in `ASSIGNMENT.md`.

## Deliverables checklist

PR with at least 3 standalone commits; updated `AGENTS.md`; spec files; unit tests for every rule including both negative rules; one Playwright test; mutation scores before and after as text; PR description with a verdict per finding; log file; `ASSIGNMENT.md` with the write-up and video link; 8 to 10 minute demo video where something runs live.
