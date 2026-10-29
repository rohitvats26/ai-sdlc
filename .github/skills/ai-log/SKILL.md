---
name: ai-log
description: How to write the per-prompt AI interaction log in this repo (one entry per prompt, model detected automatically, human review added afterwards). Use when logging a step, a follow-up prompt, a hand-typed prompt, or when the log check blocks a commit.
---

# AI log

One entry per prompt, written right after that prompt finishes. Log file: `docs/ai-log/ai-log.jsonl`. Full guide: `docs/ai-log/SCHEMA.md`.

## Commands (use `python3` if `python` is not found)
- Step prompt: `python scripts/ai_log.py add --prompt-ref <step> --action "<real thing you did>" --tool-used "<tool>" --run-tests "mvn -q test"`
- Follow-up prompt: `python scripts/ai_log.py add --parent last --prompt "<exact words>" --action "<what you did>"`
- Hand-typed prompt: `python scripts/ai_log.py add --prompt "<exact words>" --stage <spec|implement|test|e2e|review|docs> --action "..."`
- Human review, right after (the human runs this): `python scripts/ai_log.py annotate last --human-correction "..." --human-decision "..." --validation "..." --outcome successful`

## Rules
- Never pass `--model`: it is read from the Copilot Chat log. If detection fails, show the message; do not guess. Check with `python scripts/ai_log.py detect-model`.
- One `--action` per real thing done. `--skill`, `--subagent`, `--mcp` only for ones that really ran in this chat (for example `--skill "approval-tests|custom|how to write refusal tests|explicit"`).
- Never invent a prompt, tool, skill or result. Copy prompts word for word. Do not edit `docs/ai-log/` by hand.
- Leave human fields empty: they record the human's review and corrections.
- Entries start as `partially_completed`; only the human sets `successful` after checking.

## If the commit is blocked
"No AI log entry since the last commit": log the prompt you just ran, then commit again. `AI_LOG_SKIP=1` only for a commit with no AI work.
