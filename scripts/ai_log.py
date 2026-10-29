#!/usr/bin/env python3
"""Structured AI interaction log (JSONL) with a readable markdown summary.

One JSON object per line in docs/ai-log/ai-log.jsonl. Commands:

  config       set default tool and mode once (docs/ai-log/config.json); the model is detected, never stored
  detect-model show the model found in the Copilot Chat log
  add          append ONE entry per prompt, right after it finishes (evidence from git and test reports is automatic)
  check-commit fail when staged work has no AI log entry since the last commit (used by pre-commit)
  annotate     add human intervention, validation or outcome to an existing entry
  auto-commit  append an evidence-only entry for the latest git commit (used by .githooks/post-commit)
  import-chat  turn a Copilot Chat export (JSON) into entries, one per request (best effort)
  validate     check the log: required fields, allowed values, evidence, honesty warnings
  render       write docs/ai-interaction-log.md (summary, timeline, details)

Only log what really happened. Fields you cannot know are left empty rather than invented.
Run `python3 scripts/ai_log.py <command> --help` for options.
"""
import argparse, datetime, glob, json, os, re, subprocess, sys
import xml.etree.ElementTree as ET

LOG = os.path.join("docs", "ai-log", "ai-log.jsonl")
SUMMARY = os.path.join("docs", "ai-interaction-log.md")
HEADER = os.path.join("docs", "ai-log", "HEADER.md")
SCHEMA_VERSION = 2

MODES = {"ask", "plan", "agent", "edit", "n/a"}
AGENT_TYPES = {"built-in", "custom", "sub-agent", "none"}
SKILL_TYPES = {"built-in", "custom"}
INVOCATIONS = {"automatic", "explicit"}
SUBAGENT_STATUS = {"completed", "failed", "partial"}
STATUSES = {"applied", "partially_applied", "rejected", "reworked", "info"}
OUTCOMES = {"successful", "partially_completed", "rework_required"}
SOURCES = {"manual", "git-hook", "chat-export"}

REQUIRED = ["schema_version", "id", "timestamp", "session_id", "source", "stage", "agent", "agent_name",
            "agent_type", "ai_tool", "model", "mode", "related_ids", "parent_task", "context", "request",
            "prompts", "custom_instructions_followed", "skills_used", "subagents_used", "mcp_tools_used",
            "tools_used", "ai_actions", "suggestion", "human_intervention", "human_decision",
            "action_verification", "limitation", "execution_evidence", "status", "outcome", "artifacts"]


CONFIG = os.path.join("docs", "ai-log", "config.json")
PROMPT_DIR = os.path.join(".github", "prompts")
STAGE_BY_PROMPT = {"1": "spec", "2": "implement", "3": "implement", "4": "test",
                   "5": "e2e", "6": "review", "7": "docs"}
CONFIG_KEYS = ("tool", "mode", "agent_type", "agent_name")


# ---------------------------------------------------------------- helpers
def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def slug(text, limit=40):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:limit].strip("-") or "entry"


def git(*args):
    try:
        out = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=20)
        return out.stdout.rstrip("\n") if out.returncode == 0 else ""
    except Exception:
        return ""


def read_log():
    if not os.path.exists(LOG):
        return []
    rows = []
    with open(LOG, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    sys.exit(f"{LOG}: line {number} is not valid JSON: {exc}")
    return rows


def write_log(rows):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def append(row):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_config():
    if os.path.exists(CONFIG):
        with open(CONFIG, encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def last_manual_entry():
    rows = [r for r in read_log() if r.get("source") != "git-hook"]
    return rows[-1] if rows else None


def load_prompt_ref(name):
    """Read .github/prompts/<name>.prompt.md. Returns name, path, description and the prompt text."""
    name = name.lstrip("/").replace(".prompt.md", "")
    path = os.path.join(PROMPT_DIR, name + ".prompt.md")
    if not os.path.exists(path):
        sys.exit(f"prompt file not found: {path}")
    with open(path, encoding="utf-8") as handle:
        raw = handle.read()
    match = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    front, body = (match.group(1), match.group(2).strip()) if match else ("", raw.strip())
    desc = re.search(r"^description:\s*(.*)$", front, re.M)
    return {"name": name, "path": path.replace(os.sep, "/"), "description": desc.group(1).strip() if desc else name,
            "text": body}


def _copilot_log_roots():
    override = os.environ.get("COPILOT_LOG_DIR")
    if override:
        return [override]
    home = os.path.expanduser("~")
    appdata = os.environ.get("APPDATA")
    roots = []
    for product in ("Code", "Code - Insiders", "VSCodium"):
        if appdata:
            roots.append(os.path.join(appdata, product, "logs"))
        roots.append(os.path.join(home, "Library", "Application Support", product, "logs"))
        roots.append(os.path.join(home, ".config", product, "logs"))
    return [r for r in roots if os.path.isdir(r)]


CCREQ = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:\.\d+)?\s+\[\w+\]\s+ccreq:\S+\s*\|\s*\w+\s*\|\s*([^|]+?)\s*\|[^|]*\|\s*\[([^\]]*)\]", re.M)


def detect_copilot_model():
    """Best effort: read the model of the latest chat request from VS Code's 'GitHub Copilot Chat' log.

    Returns {"model", "at", "file", "kind"} or None. Prefers chat-panel requests over helper calls (titles etc.).
    The log format can change between Copilot versions; if nothing is found, pass --model or set AI_LOG_MODEL.
    """
    files = []
    for root in _copilot_log_roots():
        base = root.rstrip(os.sep).count(os.sep)
        for dirpath, _dirs, names in os.walk(root):
            if dirpath.count(os.sep) - base > 7:
                continue
            for name in names:
                if name.lower().startswith("github copilot chat") and name.lower().endswith(".log"):
                    full = os.path.join(dirpath, name)
                    files.append((os.path.getmtime(full), full))
    for _mtime, path in sorted(files, reverse=True):
        try:
            with open(path, "rb") as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                handle.seek(max(0, size - 3_000_000))
                text = handle.read().decode("utf-8", errors="replace")
        except OSError:
            continue
        hits = CCREQ.findall(text)
        panel = [h for h in hits if h[2].startswith("panel/")]
        chosen = (panel or hits or [None])[-1]
        if chosen:
            return {"model": chosen[1], "at": chosen[0], "file": path, "kind": chosen[2]}
    return None


def resolve_model(explicit):
    """Order: --model, AI_LOG_MODEL, Copilot Chat log. Returns (model, source, detected_at)."""
    if explicit:
        return explicit, "explicit", None
    if os.environ.get("AI_LOG_MODEL"):
        return os.environ["AI_LOG_MODEL"], "env", None
    found = detect_copilot_model()
    if found:
        return found["model"], "copilot-chat-log", found["at"]
    return None, None, None


def cmd_detect_model(_args):
    found = detect_copilot_model()
    if not found:
        print("No Copilot Chat log found or no chat request in it. Use --model \"<name from the model picker>\" "
              "or set AI_LOG_MODEL. Looked in: " + (", ".join(_copilot_log_roots()) or "no VS Code log folder"))
        sys.exit(1)
    print(f"model: {found['model']}\nrequest time: {found['at']} (local time)\nrequest kind: {found['kind']}\nlog file: {found['file']}")


def split_parts(text, names, defaults):
    """'a|b|c' -> dict(names[i]=part). Missing parts take defaults."""
    parts = [p.strip() for p in text.split("|")]
    out = dict(defaults)
    for key, value in zip(names, parts):
        if value:
            out[key] = value
    return out


# ---------------------------------------------------------------- automatic evidence
def test_evidence():
    """Sum the Maven surefire XML reports, if present. Returns None when there are none."""
    files = glob.glob(os.path.join("target", "surefire-reports", "TEST-*.xml"))
    if not files:
        return None
    total = failures = errors = skipped = 0
    newest = 0.0
    for path in files:
        try:
            suite = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        total += int(suite.get("tests", 0))
        failures += int(suite.get("failures", 0))
        errors += int(suite.get("errors", 0))
        skipped += int(suite.get("skipped", 0))
        newest = max(newest, os.path.getmtime(path))
    passed = total - failures - errors - skipped
    return {"source": "target/surefire-reports", "tests": total, "passed": passed, "failed": failures,
            "errors": errors, "skipped": skipped,
            "report_time": iso(datetime.datetime.fromtimestamp(newest, datetime.timezone.utc)) if newest else None}


def run_tests(command):
    """Optionally run the test command and record the real exit code."""
    started = now_utc()
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return {"command": command, "exit_code": result.returncode, "started": iso(started), "finished": iso(now_utc())}


def changed_files(since=None):
    files = []
    if since:
        files = git("diff", "--name-only", since, "HEAD").splitlines()
    status = git("status", "--porcelain").splitlines()
    files += [line[3:].strip().strip('"') for line in status if len(line) > 3]
    if not files:
        files = git("show", "--name-only", "--format=", "HEAD").splitlines()
    seen, out = set(), []
    for name in files:
        if name and name not in seen and not name.startswith("docs/ai-log/") and name != "docs/ai-interaction-log.md":
            seen.add(name)
            out.append(name)
    return out


def evidence(args=None, files=None):
    since = getattr(args, "since", None) if args else None
    commands = list(getattr(args, "command_run", None) or []) if args else []
    ran = None
    if args is not None and getattr(args, "run_tests", None):
        ran = run_tests(args.run_tests)
        commands.append(args.run_tests)
    return {"files_changed": files if files is not None else changed_files(since),
            "commit": git("rev-parse", "--short", "HEAD") or None,
            "commit_subject": git("log", "-1", "--format=%s") or None,
            "branch": git("rev-parse", "--abbrev-ref", "HEAD") or None,
            "tests": test_evidence(), "test_run": ran, "commands_run": commands}


# ---------------------------------------------------------------- building entries
def prompt_texts(args):
    texts = list(args.prompt or [])
    if args.prompts_file:
        with open(args.prompts_file, encoding="utf-8") as handle:
            texts += [chunk.strip() for chunk in re.split(r"^---\s*$", handle.read(), flags=re.M) if chunk.strip()]
    return texts


def human_from(args):
    return {"changes_made": list(args.human_change or []), "decisions": list(args.human_decision or []),
            "corrections": list(args.human_correction or []), "validation": list(args.validation or [])}


def new_entry(args):
    cfg = load_config()
    stamp = now_utc()
    refs = [load_prompt_ref(n) for n in (args.prompt_ref or [])]
    texts = prompt_texts(args)

    parent = args.parent
    parent_row = None
    if parent == "last":
        parent_row = last_manual_entry()
        if not parent_row:
            sys.exit("no earlier entry to follow up on; log the first prompt without --parent")
        parent = parent_row["id"]
    elif parent:
        parent_row = next((r for r in read_log() if r["id"] == parent), None)

    prompts = []
    for ref in refs:
        prompts.append({"seq": len(prompts) + 1, "role": "user",
                        "kind": "follow-up" if (prompts or parent) else "initial",
                        "text": "/" + ref["name"], "prompt_file": ref["path"], "prompt_file_text": ref["text"]})
    for text in texts:
        prompts.append({"seq": len(prompts) + 1, "role": "user",
                        "kind": "follow-up" if (prompts or parent) else "initial", "text": text})

    stage = args.stage or (STAGE_BY_PROMPT.get(refs[0]["name"][:1]) if refs else None) \
        or (parent_row["stage"] if parent_row else None)
    request = args.request or (refs[0]["description"] if refs else None) \
        or (texts[0].strip().splitlines()[0][:100] if texts else None)
    tool = args.tool or cfg.get("tool")
    mode = args.mode or cfg.get("mode")
    model, model_source, model_detected_at = resolve_model(args.model)
    if not stage or not request:
        sys.exit("give --prompt-ref or --prompt, or --stage and --request")
    if not tool or not mode:
        sys.exit("tool and mode are not set. Run once: python scripts/ai_log.py config --tool \"GitHub Copilot\" --mode agent")
    if not model or str(model).startswith("<"):
        sys.exit("Could not detect the Copilot model from the Copilot Chat log. Check it with: python scripts/ai_log.py detect-model. "
                 "Or pass the name shown in the chat model picker: --model \"<name>\" (or set AI_LOG_MODEL). Do not guess.")

    instructions = list(args.instruction or [])
    for ref in refs:
        if ref["path"] not in instructions:
            instructions.append(ref["path"])
    related = list(args.related or [])
    if parent and parent not in related:
        related.append(parent)

    entry = {
        "schema_version": SCHEMA_VERSION,
        "id": "",
        "timestamp": iso(stamp),
        "session_id": args.session or os.environ.get("AI_LOG_SESSION") or stamp.strftime("%Y%m%d"),
        "source": "manual",
        "stage": stage,
        "agent": args.agent or mode,
        "agent_name": args.agent_name or cfg.get("agent_name") or "Agent",
        "agent_type": args.agent_type or cfg.get("agent_type") or "built-in",
        "ai_tool": tool,
        "model": model,
        "model_source": model_source,
        "model_detected_at": model_detected_at,
        "mode": mode,
        "related_ids": related,
        "parent_task": parent,
        "context": args.context or "Assignment for AI in SDLC",
        "request": request,
        "prompts": prompts,
        "custom_instructions_followed": instructions,
        "skills_used": [split_parts(x, ["name", "type", "purpose", "invocation"],
                                    {"name": "", "type": "custom", "purpose": "", "invocation": "explicit"})
                        for x in (args.skill or [])],
        "subagents_used": [split_parts(x, ["name", "type", "task", "status"],
                                       {"name": "", "type": "custom", "task": "", "status": "completed"})
                           for x in (args.subagent or [])],
        "mcp_tools_used": [split_parts(x, ["server", "tool", "purpose"], {"server": "", "tool": "", "purpose": ""})
                           for x in (args.mcp or [])],
        "tools_used": list(args.tool_used or []),
        "ai_actions": list(args.action or []),
        "suggestion": args.suggestion,
        "human_intervention": human_from(args),
        "human_decision": args.decision_summary,
        "action_verification": args.verification,
        "limitation": args.limitation,
        "execution_evidence": evidence(args),
        "status": args.status,
        "outcome": args.outcome,
        "artifacts": list(args.artifact or []),
    }
    entry["id"] = f"{stamp.strftime('%Y%m%dT%H%M%SZ')}-{slug(entry['agent_name'])}-{slug(entry['request'])}"
    return entry


def add_common(p, required):
    """Options shared by add and annotate."""
    g = p.add_argument_group("what happened")
    g.add_argument("--prompt-ref", action="append", help="name of a prompt file in .github/prompts, for example 2-single-approver")
    g.add_argument("--prompt", action="append", help="exact prompt sent (repeat for follow-ups)")
    g.add_argument("--prompts-file", help="text file with prompts separated by lines containing only ---")
    g.add_argument("--action", action="append", help="what the AI did: code written, tests made, files changed")
    g.add_argument("--suggestion", help="what the AI suggested that you did or did not take")
    g.add_argument("--instruction", action="append", help="custom instruction file or rule that was followed")
    g.add_argument("--skill", action="append", help="'name|built-in or custom|purpose|automatic or explicit'")
    g.add_argument("--subagent", action="append", help="'name|built-in or custom|task|completed, failed or partial'")
    g.add_argument("--mcp", action="append", help="'server|tool|purpose'")
    g.add_argument("--tool-used", action="append", help="other tool or capability used (terminal, search, edit...)")
    h = p.add_argument_group("human oversight")
    h.add_argument("--human-change", action="append", help="manual change you made to the AI output")
    h.add_argument("--human-decision", action="append", help="decision you made (accepted, rejected, chose option)")
    h.add_argument("--human-correction", action="append", help="mistake you found and corrected")
    h.add_argument("--validation", action="append", help="how you checked it (command, test, manual check)")
    h.add_argument("--decision-summary", help="one-line summary of your decision")
    h.add_argument("--verification", help="one-line summary of how the action was verified")
    h.add_argument("--limitation", help="what did not work or could not be checked")
    e = p.add_argument_group("evidence and result")
    e.add_argument("--run-tests", metavar="CMD", help="run this test command now and record the real exit code")
    e.add_argument("--command-run", action="append", help="a command you ran that is not recorded elsewhere")
    e.add_argument("--since", help="git revision: list files changed since it (default: working tree, else last commit)")
    e.add_argument("--artifact", action="append", help="file produced (spec, test, report...)")
    e.add_argument("--status", choices=sorted(STATUSES), default="applied" if required else None)
    e.add_argument("--outcome", choices=sorted(OUTCOMES), default="partially_completed" if required else None,
                   help="default partially_completed until a human has validated: then 'annotate last --outcome successful'")


# ---------------------------------------------------------------- commands
def cmd_add(args):
    entry = new_entry(args)
    append(entry)
    print("logged", entry["id"])


def cmd_annotate(args):
    rows = read_log()
    if args.id == "last":
        manual = [r for r in rows if r.get("source") != "git-hook"]
        target = manual[-1:]
    else:
        target = [r for r in rows if r["id"] == args.id or r["id"].endswith(args.id)]
    if len(target) != 1:
        sys.exit(f"expected exactly one entry matching '{args.id}', found {len(target)}")
    row = target[0]
    human = human_from(args)
    for key in ("changes_made", "decisions", "corrections", "validation"):
        row["human_intervention"][key] += human[key]
    row["ai_actions"] += list(args.action or [])
    row["artifacts"] += list(args.artifact or [])
    for field, value in (("suggestion", args.suggestion), ("human_decision", args.decision_summary),
                         ("action_verification", args.verification), ("limitation", args.limitation),
                         ("status", args.status), ("outcome", args.outcome)):
        if value:
            row[field] = value
    if args.limitation is None and row.get("limitation", "") and "Imported from a chat export" in row["limitation"] \
            and any(human.values()):
        row["limitation"] = None
    if args.run_tests or args.command_run or args.since:
        row["execution_evidence"] = evidence(args)
    write_log(rows)
    print("annotated", row["id"])


def cmd_config(args):
    cfg = load_config()
    for key in CONFIG_KEYS:
        value = getattr(args, key, None)
        if value:
            cfg[key] = value
    if any(getattr(args, key, None) for key in CONFIG_KEYS):
        os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
        with open(CONFIG, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(cfg, handle, indent=2)
            handle.write("\n")
    print(json.dumps(cfg, indent=2) if cfg else "no defaults set yet")


def cmd_check_commit(_args):
    """Used by pre-commit: a commit with real changes needs at least one AI log entry made since the last commit."""
    staged = git("diff", "--cached", "--name-only").splitlines()
    work = [f for f in staged if f and not f.startswith("docs/ai-log/") and f != "docs/ai-interaction-log.md"]
    if not work:
        return
    if os.environ.get("AI_LOG_SKIP") == "1":
        print("warning: AI log check skipped (AI_LOG_SKIP=1)")
        return
    last = git("log", "-1", "--format=%ct")
    since = int(last) if last.isdigit() else 0
    fresh = []
    for row in read_log():
        if row.get("source") == "git-hook":
            continue
        try:
            moment = int(datetime.datetime.strptime(row["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
                         .replace(tzinfo=datetime.timezone.utc).timestamp())
        except (KeyError, ValueError):
            continue
        if moment > since:
            fresh.append(row)
    if not fresh:
        sys.exit("No AI log entry was written since the last commit. Log each prompt right after it finishes, "
                 "for example: python scripts/ai_log.py add --prompt-ref <step> --action \"...\"  "
                 "(see docs/ai-log/SCHEMA.md). If this commit has no AI work, set AI_LOG_SKIP=1 for this commit.")


def cmd_auto_commit(_args):
    """Evidence-only entry for the latest commit. No AI claims are made."""
    stamp = now_utc()
    subject = git("log", "-1", "--format=%s") or "commit"
    files = [f for f in git("show", "--name-only", "--format=", "HEAD").splitlines()
             if f and not f.startswith("docs/ai-log/")]
    entry = {
        "schema_version": SCHEMA_VERSION, "id": f"{stamp.strftime('%Y%m%dT%H%M%SZ')}-git-hook-{slug(subject)}",
        "timestamp": iso(stamp), "session_id": os.environ.get("AI_LOG_SESSION") or stamp.strftime("%Y%m%d"),
        "source": "git-hook", "stage": "commit", "agent": "none", "agent_name": "git post-commit hook",
        "agent_type": "none", "ai_tool": "n/a", "model": "n/a", "model_source": None, "model_detected_at": None,
        "mode": "n/a", "related_ids": [],
        "parent_task": None, "context": "Automatic evidence for a commit", "request": f"Commit: {subject}",
        "prompts": [], "custom_instructions_followed": [], "skills_used": [], "subagents_used": [],
        "mcp_tools_used": [], "tools_used": ["git"], "ai_actions": [], "suggestion": None,
        "human_intervention": {"changes_made": [], "decisions": [], "corrections": [], "validation": []},
        "human_decision": None, "action_verification": None, "limitation": None,
        "execution_evidence": evidence(None, files=files),
        "status": "info", "outcome": "successful", "artifacts": [],
    }
    append(entry)
    print("logged", entry["id"])


def _text_of(parts):
    out = []
    for part in parts or []:
        if isinstance(part, str):
            out.append(part)
        elif isinstance(part, dict):
            value = part.get("value") or part.get("content") or part.get("text")
            if isinstance(value, dict):
                value = value.get("value") or value.get("text")
            if isinstance(value, str):
                out.append(value)
    return "".join(out).strip()


def cmd_import_chat(args):
    """Best-effort import of a Copilot Chat export. Shapes differ between versions, so check the result."""
    with open(args.file, encoding="utf-8") as handle:
        data = json.load(handle)
    requests = data.get("requests") if isinstance(data, dict) else data
    if not isinstance(requests, list) or not requests:
        sys.exit("no 'requests' list found in that file; export with 'Chat: Export Chat...' in VS Code")
    count = 0
    for request in requests:
        message = request.get("message") or {}
        prompt = message.get("text") if isinstance(message, dict) else message
        prompt = prompt or request.get("prompt") or ""
        if not prompt:
            continue
        reply = _text_of(request.get("response"))
        stamp_ms = request.get("timestamp")
        stamp = (datetime.datetime.fromtimestamp(stamp_ms / 1000, datetime.timezone.utc).replace(microsecond=0)
                 if isinstance(stamp_ms, (int, float)) else now_utc())
        agent = request.get("agent") or {}
        agent_name = ((agent.get("name") or agent.get("id")) if isinstance(agent, dict) else str(agent)) \
            or args.agent_name or "default"
        model = request.get("modelId") or (data.get("model") if isinstance(data, dict) else None)
        model_source = "chat-export" if model else None
        if not model:
            model, model_source, _seen = resolve_model(args.model)
        if not model:
            model, model_source = "unknown", "unknown"
        entry = {
            "schema_version": SCHEMA_VERSION, "id": "", "timestamp": iso(stamp),
            "session_id": args.session or os.environ.get("AI_LOG_SESSION") or stamp.strftime("%Y%m%d"),
            "source": "chat-export", "stage": args.stage, "agent": args.mode, "agent_name": agent_name,
            "agent_type": args.agent_type, "ai_tool": args.tool, "model": model, "model_source": model_source,
            "model_detected_at": None, "mode": args.mode,
            "related_ids": [], "parent_task": None, "context": args.context or "Assignment for AI in SDLC",
            "request": prompt.strip().splitlines()[0][:120],
            "prompts": [{"seq": 1, "role": "user", "kind": "initial", "text": prompt}],
            "custom_instructions_followed": [], "skills_used": [], "subagents_used": [], "mcp_tools_used": [],
            "tools_used": [], "ai_actions": ([f"Reply (first 400 chars): {reply[:400]}"] if reply else []),
            "suggestion": None,
            "human_intervention": {"changes_made": [], "decisions": [], "corrections": [], "validation": []},
            "human_decision": None, "action_verification": None,
            "limitation": "Imported from a chat export: add human intervention and validation with 'annotate'.",
            "execution_evidence": evidence(None), "status": "applied", "outcome": "partially_completed",
            "artifacts": [],
        }
        entry["id"] = f"{stamp.strftime('%Y%m%dT%H%M%SZ')}-{slug(agent_name)}-{slug(entry['request'])}-{count + 1}"
        append(entry)
        count += 1
    print(f"imported {count} requests from {args.file}; now run 'annotate' on each with what you changed and checked")


def validate_rows(rows):
    errors, warnings, seen = [], [], set()
    if not rows:
        return ["log is empty"], []
    for n, row in enumerate(rows, 1):
        where = f"entry {n} ({row.get('id', '?')})"
        missing = [k for k in REQUIRED if k not in row]
        if missing:
            errors.append(f"{where}: missing fields {missing}")
            continue
        if row["id"] in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(row["id"])
        try:
            datetime.datetime.strptime(row["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            errors.append(f"{where}: timestamp must look like 2026-10-19T06:35:42Z")
        for field, allowed in (("mode", MODES), ("agent_type", AGENT_TYPES), ("status", STATUSES),
                               ("outcome", OUTCOMES), ("source", SOURCES)):
            if row[field] not in allowed:
                errors.append(f"{where}: {field} '{row[field]}' not in {sorted(allowed)}")
        for skill in row["skills_used"]:
            if skill.get("type") not in SKILL_TYPES or skill.get("invocation") not in INVOCATIONS or not skill.get("name"):
                errors.append(f"{where}: bad skill entry {skill}")
        for sub in row["subagents_used"]:
            if sub.get("type") not in SKILL_TYPES or sub.get("status") not in SUBAGENT_STATUS or not sub.get("name"):
                errors.append(f"{where}: bad subagent entry {sub}")
        for mcp in row["mcp_tools_used"]:
            if not mcp.get("server") or not mcp.get("tool"):
                errors.append(f"{where}: MCP entry needs server and tool")
        if row["source"] != "git-hook":
            if not row["prompts"]:
                errors.append(f"{where}: no prompt recorded; log the actual prompt text")
            if not row["ai_tool"] or not row["model"]:
                errors.append(f"{where}: ai_tool and model are required")
            if row.get("model_source") == "explicit":
                warnings.append(f"{where}: model was typed by hand; prefer the automatic detection when it works")
            if str(row["model"]).lower() in ("unknown", "?", ""):
                warnings.append(f"{where}: model is '{row['model']}'; name the real model")
            hi, ev = row["human_intervention"], row["execution_evidence"]
            has_check = bool(hi["validation"]) or bool(row["action_verification"]) or bool(ev.get("tests")) \
                or bool(ev.get("test_run"))
            if row["status"] in ("applied", "partially_applied", "reworked") and not has_check:
                warnings.append(f"{where}: applied but no validation or test evidence")
            if row["limitation"] and "Imported from a chat export" in row["limitation"]:
                warnings.append(f"{where}: imported entry still needs 'annotate' (human review and outcome)")
    manual = [r for r in rows if all(k in r for k in REQUIRED) and r["source"] != "git-hook"]
    if manual and not any(any(r["human_intervention"].values()) for r in manual):
        warnings.append("no entry records any human intervention; the log should show your review and corrections")
    return errors, warnings


def cmd_validate(_args):
    rows = read_log()
    errors, warnings = validate_rows(rows)
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("error:", e, file=sys.stderr)
    if errors:
        sys.exit(1)
    print(f"{LOG}: {len(rows)} entries valid, {len(warnings)} warnings")


def cmd_render(_args):
    rows = read_log()
    manual = [r for r in rows if r["source"] != "git-hook"]
    head = open(HEADER, encoding="utf-8").read().rstrip() if os.path.exists(HEADER) else "# AI interaction log"

    def names(seq):
        return sorted({(x if isinstance(x, str) else x.get("name") or x.get("tool")) for x in seq})

    def tally(field):
        return ", ".join(f"{v} x{sum(1 for r in manual if r[field] == v)}" for v in sorted({r[field] for r in manual})) or "none"

    out = [head, "", "Generated from `docs/ai-log/ai-log.jsonl` by `python3 scripts/ai_log.py render`. Do not edit by hand.", "",
           "## Summary", "",
           f"- Entries: {len(rows)} ({len(manual)} AI interactions, {len(rows) - len(manual)} automatic commit records)",
           "- Tools and models: " + (", ".join(sorted({f"{r['ai_tool']} / {r['model']}" for r in manual})) or "none"),
           f"- Modes used: {tally('mode')}",
           f"- Agent types: {tally('agent_type')}",
           "- Skills used: " + (", ".join(names(s for r in manual for s in r["skills_used"])) or "none"),
           "- Sub-agents used: " + (", ".join(names(s for r in manual for s in r["subagents_used"])) or "none"),
           "- MCP tools used: " + (", ".join(names(s for r in manual for s in r["mcp_tools_used"])) or "none"),
           f"- Interactions with human intervention recorded: {sum(1 for r in manual if any(r['human_intervention'].values()))} of {len(manual)}",
           f"- Interactions with validation evidence: {sum(1 for r in manual if r['human_intervention']['validation'] or r['action_verification'] or r['execution_evidence'].get('tests'))} of {len(manual)}",
           f"- Outcomes: {tally('outcome')}",
           "", "## Timeline", "", "| # | Time (UTC) | Stage | Tool / model | Mode | Agent | Request | Status | Outcome |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for n, r in enumerate(rows, 1):
        out.append(f"| {n} | {r['timestamp']} | {r['stage']} | {r['ai_tool']} / {r['model']} | {r['mode']} | "
                   f"{r['agent_name']} ({r['agent_type']}) | {r['request'][:70]} | {r['status']} | {r['outcome']} |")
    out += ["", "## Details", ""]
    for n, r in enumerate(rows, 1):
        ev, hi = r["execution_evidence"], r["human_intervention"]
        out += [f"### {n}. {r['request']}", f"`{r['id']}` - source: {r['source']}", ""]
        src = {"copilot-chat-log": f"auto-detected from the Copilot Chat log at {r.get('model_detected_at')}", "chat-export": "from the chat export",
               "env": "from AI_LOG_MODEL", "explicit": "typed by hand"}.get(r.get("model_source") or "", "")
        out.append(f"- **Tool / model / mode:** {r['ai_tool']} / {r['model']}" + (f" ({src})" if src else "") + f" / {r['mode']}; agent {r['agent_name']} ({r['agent_type']})")
        out.append(f"- **Stage / session:** {r['stage']} / {r['session_id']}")
        for p in r["prompts"]:
            out.append(f"- **Prompt {p['seq']} ({p['kind']}):** {p['text'].strip()[:600]}")
        for label, items in (("Custom instructions followed", r["custom_instructions_followed"]),
                             ("Tools used", r["tools_used"]), ("AI actions", r["ai_actions"])):
            if items:
                out.append(f"- **{label}:** " + "; ".join(items))
        if r["skills_used"]:
            out.append("- **Skills:** " + "; ".join(f"{s['name']} ({s['type']}, {s['invocation']}): {s['purpose']}" for s in r["skills_used"]))
        if r["subagents_used"]:
            out.append("- **Sub-agents:** " + "; ".join(f"{s['name']} ({s['type']}, {s['status']}): {s['task']}" for s in r["subagents_used"]))
        if r["mcp_tools_used"]:
            out.append("- **MCP:** " + "; ".join(f"{m['server']}/{m['tool']}: {m['purpose']}" for m in r["mcp_tools_used"]))
        if r["suggestion"]:
            out.append(f"- **AI suggestion:** {r['suggestion']}")
        for label, key in (("manual changes", "changes_made"), ("decisions", "decisions"),
                           ("corrections", "corrections"), ("validation", "validation")):
            if hi[key]:
                out.append(f"- **Human, {label}:** " + "; ".join(hi[key]))
        if r["human_decision"]:
            out.append(f"- **Human decision (summary):** {r['human_decision']}")
        if r["action_verification"]:
            out.append(f"- **Verification:** {r['action_verification']}")
        if r["limitation"]:
            out.append(f"- **Limitation:** {r['limitation']}")
        t = ev.get("tests")
        line = (f"- **Evidence:** commit {ev.get('commit')} on {ev.get('branch')}; files: "
                f"{', '.join(ev.get('files_changed') or []) or 'none recorded'}")
        if t:
            line += f"; tests {t['passed']}/{t['tests']} passed, {t['failed']} failed, {t['errors']} errors (report {t['report_time']})"
        if ev.get("test_run"):
            line += f"; ran `{ev['test_run']['command']}` exit {ev['test_run']['exit_code']}"
        out.append(line)
        if r["artifacts"]:
            out.append("- **Artifacts:** " + ", ".join(r["artifacts"]))
        out.append(f"- **Status / outcome:** {r['status']} / {r['outcome']}")
        out.append("")
    with open(SUMMARY, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(out) + "\n")
    print(f"rendered {len(rows)} entries -> {SUMMARY}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="append an interaction (one per prompt, right after it finishes)")
    a.add_argument("--stage", help="setup, spec, implement, test, e2e, review, docs... (inferred from --prompt-ref)")
    a.add_argument("--request", help="what you asked for, one line (inferred from --prompt-ref or --prompt)")
    a.add_argument("--tool", help="AI tool (default from config)")
    a.add_argument("--model", help="model name. Normally NOT needed: it is detected from the Copilot Chat log")
    a.add_argument("--mode", choices=sorted(MODES), help="ask, plan, agent or edit (default from config)")
    a.add_argument("--agent-type", choices=sorted(AGENT_TYPES), help="built-in, custom or sub-agent (default from config)")
    a.add_argument("--agent-name", help="agent name, for example 'Agent' or a custom agent file name")
    a.add_argument("--agent", help="short agent label (defaults to the mode)")
    a.add_argument("--context")
    a.add_argument("--session")
    a.add_argument("--related", action="append", help="id of a related entry")
    a.add_argument("--parent", help="id of the parent entry, or 'last' to log a follow-up prompt")
    add_common(a, required=True)
    a.set_defaults(fn=cmd_add)

    n = sub.add_parser("annotate", help="add human oversight or outcome to an entry")
    n.add_argument("id", help="entry id, or the end of it")
    add_common(n, required=False)
    n.set_defaults(fn=cmd_annotate)

    c0 = sub.add_parser("config", help="set default tool and mode once (the model is detected, never stored)")
    c0.add_argument("--tool")
    c0.add_argument("--mode", choices=sorted(MODES))
    c0.add_argument("--agent-type", dest="agent_type", choices=sorted(AGENT_TYPES))
    c0.add_argument("--agent-name", dest="agent_name")
    c0.set_defaults(fn=cmd_config)

    sub.add_parser("detect-model", help="show the Copilot model found in the Copilot Chat log").set_defaults(fn=cmd_detect_model)

    sub.add_parser("check-commit", help="fail if staged work has no AI log entry since the last commit").set_defaults(fn=cmd_check_commit)

    sub.add_parser("auto-commit", help="evidence-only entry for the latest commit (git hook)").set_defaults(fn=cmd_auto_commit)

    i = sub.add_parser("import-chat", help="import a Copilot Chat export (JSON)")
    i.add_argument("file")
    i.add_argument("--stage", required=True)
    i.add_argument("--tool", default="GitHub Copilot")
    i.add_argument("--model", help="only used when the export has no model; otherwise auto-detected")
    i.add_argument("--mode", default="agent", choices=sorted(MODES))
    i.add_argument("--agent-type", default="built-in", choices=sorted(AGENT_TYPES))
    i.add_argument("--agent-name")
    i.add_argument("--context")
    i.add_argument("--session")
    i.set_defaults(fn=cmd_import_chat)

    sub.add_parser("validate", help="check the log").set_defaults(fn=cmd_validate)
    sub.add_parser("render", help="write the markdown summary").set_defaults(fn=cmd_render)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
