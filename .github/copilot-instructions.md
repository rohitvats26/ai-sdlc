# Copilot instructions

Read `AGENTS.md` first: it holds the approval rules, layering, commands and review expectations. The spec lives in `openspec/changes/add-approval-limits-by-role/` once created.

## Skills
Custom skills in `.github/skills/`: `approval-rules`, `approval-tests`, `playwright-e2e`, `review-findings`, `ai-log`. Use the one that matches the task; each step prompt names the ones it needs.

## Hard rules
- Money is `BigDecimal`, compared with `compareTo`. Never `double`, `float`, or `equals` on amounts.
- Rules live in the `domain` package (a pure policy plus the service). Never in controllers.
- A refused approval must change nothing. Every refusal test proves the invoice is unchanged.
- Do not weaken a rule or a test to make a test pass. Stop and report instead.

## Finish protocol (the end of every step prompt in `.github/prompts/` points here; more detail in skill `ai-log`, `.github/skills/ai-log/SKILL.md`)
1. **Log the prompt**, as your last action before you say you are done. One entry per prompt, using the exact command at the end of the prompt (`python scripts/ai_log.py add --prompt-ref <step> ...`).
   - One `--action` per real thing you did: files created or changed, tests added, commands run.
   - Add `--skill "name|custom|purpose|explicit"`, `--subagent "name|custom|task|completed"` or `--mcp "server|tool|purpose"` only for ones that really ran in this chat. Never guess.
   - Never pass `--model`: it is detected from the Copilot Chat log. If the command says it cannot detect the model, show me the message and stop.
   - Never invent a prompt, tool, skill, test result or model name. Copy my words exactly.
   - Leave all human fields empty: I add my review with `annotate last`.
   - If `python` is not found use `python3`. If the command fails, show me the error; do not edit `docs/ai-log/` by hand.
2. **Commit the work** right after logging, unless only `docs/ai-log/` or `docs/ai-interaction-log.md` changed.
   - `git add -A`, then `git commit -m "<type>: <what changed>" -m "Why: <the reason>"`.
   - The pre-commit hook runs the tests, the prompt linter and the log check. If it blocks the commit, fix the cause and commit again.
   - Never use `--no-verify` or `AI_LOG_SKIP`. Never push, amend or rewrite history.
   - Tell me the commit hash and message.
3. **Follow-up prompts** in the same chat: after each one finishes, log it with `python scripts/ai_log.py add --parent last --prompt "<my exact words>" --action "<what you did>"`, then commit if files changed.
4. **A prompt that was not a step prompt** (I typed it by hand) and changed files: log it the same way with `--prompt "<my exact words>" --stage <spec|implement|test|e2e|review|docs>`.
