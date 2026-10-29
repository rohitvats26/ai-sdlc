# AI log: format and how to fill it

The log is `docs/ai-log/ai-log.jsonl` (one JSON object per line). `docs/ai-interaction-log.md` is generated from it. Goal: show **how well** AI was used and how **you** checked it, not how many prompts you sent.

## The rule: one entry per prompt, written when that prompt finishes

Do not log at the end of the day or at the end of the project. Every prompt (and every follow-up) gets its own entry as soon as it is done.

1. **Once:** `python scripts/ai_log.py config --tool "GitHub Copilot" --mode agent`. Run it again if you change mode. You never set the model: it is read from Copilot Chat each time (see "Model name" below).
2. **Run a step prompt** (for example `/2-single-approver`). Its last instruction makes Copilot log the step itself with `ai_log.py add --prompt-ref 2-single-approver ...` (stage, request, prompt text, instruction file, tool, model, changed files and test results are filled in for you).
3. **Follow-up prompts:** Copilot logs each one right after it finishes: `ai_log.py add --parent last --prompt "<your exact words>" --action "..."`. Entries are linked with `parent_task` and `related_ids`.
4. **Your review, straight after:** `python scripts/ai_log.py annotate last --human-correction "..." --human-decision "..." --validation "mvn test green" --outcome successful`. Copilot's entries start as `partially_completed` until you have checked them.
5. **Commit.** Each step prompt ends by committing its own work (after logging). The pre-commit hook blocks the commit if no prompt was logged since the last commit (set `AI_LOG_SKIP=1` only for a commit with no AI work). It also refreshes `docs/ai-interaction-log.md` and adds the log files to the commit. Your `annotate` notes from step 4 are added to the next commit.
6. **If a prompt was missed:** log it yourself: `python scripts/ai_log.py add --prompt "<your exact words>" --stage <stage> --action "..."`, or `import-chat` a chat export. The pre-commit hook will not let a commit through until at least one prompt is logged.

## Commands

| Command | Use it to |
| --- | --- |
| `ai_log.py config --tool ... --mode ...` | Set the default tool and mode once (`docs/ai-log/config.json`). The model is never stored. |
| `ai_log.py detect-model` | Show which model Copilot Chat is using right now (read from its log). Run it to check the detection works on your machine. |
| `ai_log.py add --prompt-ref <name> ...` | Log one prompt. `--prompt "text"` logs a typed prompt; `--parent last` marks a follow-up. |
| `ai_log.py annotate last ...` | Add your human review, corrections, validation and outcome to the latest entry. Also accepts an entry id. |
| `ai_log.py import-chat export.json --stage <stage> --mode <ask or agent>` | Turn a Copilot Chat export into entries (best effort, see below). |
| `ai_log.py check-commit` | Used by the pre-commit hook: staged work needs a log entry since the last commit. |
| `ai_log.py validate` | Check required fields, allowed values and honesty warnings. |
| `ai_log.py render` | Rebuild the readable summary. |
| `.githooks/post-commit` | Automatically adds an evidence-only record after every commit. |

On Windows, use `python`, `py` or `python3`, whichever works. The git hooks pick one automatically.

## What is automatic and what is yours

| Detail you need to capture | How it gets in the log |
| --- | --- |
| Timestamps, session id, entry id | Automatic |
| Files changed, branch, commit, commit subject | Automatic (git) |
| Test results | Automatic from `target/surefire-reports`; `--run-tests "mvn -q test"` also records the real exit code |
| Commits | Automatic record from the post-commit hook |
| Prompts and follow-ups | `--prompt-ref` (slash prompts, text taken from the prompt file), `--prompt` (typed prompts), or `import-chat` from a chat export. Each prompt step logs itself. |
| AI model | **Detected automatically from the Copilot Chat log on every entry** (the model of the latest chat request), so it follows the model picker when you switch. Recorded with `model_source` and `model_detected_at`. |
| AI tool, mode, agent type | Tool and mode set once with `config`; override per entry with `--tool`, `--mode`, `--agent-type`, `--agent-name` |
| Skills, sub-agents, MCP tools, custom instructions | `--skill`, `--subagent`, `--mcp`, `--instruction`. Log only what really ran. |
| AI actions and outputs | `--action` (or the reply excerpt that `import-chat` stores) |
| Human intervention and validation | `--human-change`, `--human-decision`, `--human-correction`, `--validation` (always yours) |
| Outcome | Copilot starts it as `partially_completed`; you set the final `--outcome` with `annotate last` |

Honest limit: this repo cannot make Copilot write its own structured log. What is automatic is the git and test evidence. Prompts can be imported from a chat export (in VS Code, run **Chat: Export Chat...** from the Command Palette; if your version names it differently, search for "export chat"). The import expects a `requests` list and was written without a real export to test against, so look at the result and fix by hand if the shape differs. Everything about your own review is manual on purpose.

## Model name

The model is never typed or stored. Each time an entry is written, the script reads the latest chat request in VS Code's "GitHub Copilot Chat" log (under `%APPDATA%\Code\logs` on Windows) and records that model. Helper requests such as chat titles are ignored. The entry keeps `model_source` (`copilot-chat-log`) and `model_detected_at` as evidence. Order of lookup: `--model` (typed, flagged in the log) then the `AI_LOG_MODEL` environment variable, then the Copilot Chat log, then the model in a chat export. If none works, the command stops and asks you; it never guesses.

Honest limit: this reads a log file whose format can change between Copilot versions, and it was tested here only against a made-up sample, not a real Copilot install. Run `python scripts/ai_log.py detect-model` once on your machine. If it finds nothing, set the model per session: `$env:AI_LOG_MODEL = "<name shown in the model picker>"`, and it will be recorded as `env`.

## Fields

`id`, `timestamp`, `session_id`, `source` (manual, git-hook, chat-export), `stage`, `agent`, `agent_name`, `agent_type` (built-in, custom, sub-agent, none), `ai_tool`, `model`, `model_source`, `model_detected_at`, `mode` (ask, plan, agent, edit, n/a), `related_ids`, `parent_task`, `context`, `request`, `prompts` (list of `{seq, role, kind, text}`), `custom_instructions_followed`, `skills_used` (`{name, type, purpose, invocation}`), `subagents_used` (`{name, type, task, status}`), `mcp_tools_used` (`{server, tool, purpose}`), `tools_used`, `ai_actions`, `suggestion`, `human_intervention` (`{changes_made, decisions, corrections, validation}`), `human_decision`, `action_verification`, `limitation`, `execution_evidence` (`{files_changed, commit, commit_subject, branch, tests, test_run, commands_run}`), `status` (applied, partially_applied, rejected, reworked, info), `outcome` (successful, partially_completed, rework_required), `artifacts`, `schema_version`.

## Example (fictional, for format only; not part of the real log)

```json
{"schema_version":2,"id":"20261019T063542Z-implementer-single-approver-limits","timestamp":"2026-10-19T06:35:42Z","session_id":"20261019","source":"manual","stage":"implement","agent":"agent","agent_name":"implementer","agent_type":"custom","ai_tool":"GitHub Copilot","model":"<model from picker>","mode":"agent","related_ids":[],"parent_task":null,"context":"Assignment for AI in SDLC","request":"Single-approver limits","prompts":[{"seq":1,"role":"user","kind":"initial","text":"<prompt 2-single-approver, word for word>"},{"seq":2,"role":"user","kind":"follow-up","text":"Include the invoice id in the refusal message."}],"custom_instructions_followed":[".github/copilot-instructions.md"],"skills_used":[],"subagents_used":[],"mcp_tools_used":[],"tools_used":["terminal"],"ai_actions":["Created ApprovalPolicy","Added boundary tests"],"suggestion":"Compare amounts with equals","human_intervention":{"changes_made":[],"decisions":["Rejected equals, asked for compareTo"],"corrections":["BigDecimal scale bug at 50000.00"],"validation":["mvn test green"]},"human_decision":"Accepted after one correction","action_verification":"Boundary tests pass","limitation":null,"execution_evidence":{"files_changed":["src/main/java/.../ApprovalPolicy.java"],"commit":"abc1234","commit_subject":"feat: enforce limits","branch":"main","tests":{"source":"target/surefire-reports","tests":20,"passed":20,"failed":0,"errors":0,"skipped":0,"report_time":"2026-10-19T06:40:00Z"},"test_run":null,"commands_run":[]},"status":"reworked","outcome":"successful","artifacts":["src/main/java/.../ApprovalPolicy.java"]}
```

## A good entry

- The prompt is the real text, and follow-ups are included.
- It says which skills, sub-agents or MCP tools actually ran, or leaves them empty.
- It records at least one thing **you** decided, changed or corrected, and how you checked the result.
- Failures and rework are logged too; `rework_required` and `reworked` show real oversight.
