#!/usr/bin/env python3
"""Finish a step: log the prompt, then commit its work with a "what" and "why" message. One command.

  python scripts/finish.py --prompt-ref 2-single-approver --type feat \\
      --what "enforce manager and director limits" --why "approval authority must depend on role" \\
      --action "Added ApprovalPolicy" --action "Added 14 tests" --run-tests "mvn -q test"

Own options: --type, --what, --why, --no-commit. Every other option goes to `ai_log.py add`
(see docs/ai-log/SCHEMA.md): --prompt-ref, --prompt, --parent last, --action, --tool-used, --skill, ...

Safe to run again after a blocked commit: a prompt already logged since the last commit is not logged twice.
If only the AI log changed, nothing is committed.
"""
import argparse, os, subprocess, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai_log  # noqa: E402

TYPES = ["feat", "fix", "docs", "test", "chore", "refactor"]


def fail(message):
    print(f"finish: {message}", file=sys.stderr)
    sys.exit(1)


def first_prompt_text(rest):
    """The prompt text this entry would record, used to avoid logging it twice."""
    for flag, wrap in (("--prompt-ref", lambda v: "/" + v.lstrip("/").replace(".prompt.md", "")), ("--prompt", lambda v: v)):
        if flag in rest and rest.index(flag) + 1 < len(rest):
            return wrap(rest[rest.index(flag) + 1])
    return None


def already_logged(text):
    if not text:
        return False
    since = ai_log.git("log", "-1", "--format=%ct")
    since = int(since) if since.isdigit() else 0
    for row in ai_log.read_log():
        if row.get("source") == "git-hook" or not row.get("prompts"):
            continue
        import calendar, time
        moment = calendar.timegm(time.strptime(row["timestamp"], "%Y-%m-%dT%H:%M:%SZ"))
        if moment > since and row["prompts"][0]["text"] == text:
            return True
    return False


def work_changed():
    changed = []
    for line in ai_log.git("status", "--porcelain").splitlines():
        name = line[3:].strip().strip('"')
        if " -> " in name:
            name = name.split(" -> ")[-1]
        if name and not name.startswith("docs/ai-log/") and name != "docs/ai-interaction-log.md":
            changed.append(name)
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--type", required=True, choices=TYPES, help="commit type")
    parser.add_argument("--what", required=True, help="what changed, short (max 72 characters)")
    parser.add_argument("--why", required=True, help="why it changed, one sentence")
    parser.add_argument("--no-commit", action="store_true", help="log only")
    own, rest = parser.parse_known_args()

    what, why = own.what.strip(), own.why.strip()
    if not what or len(what) > 72:
        fail("--what must be 1 to 72 characters")
    if what.split(":")[0] in TYPES and ":" in what:
        fail("--what must not start with the type; give only the wording after 'type: '")
    if len(why) < 15:
        fail("--why must be a real sentence (at least 15 characters)")
    if "--model" in rest:
        fail("do not pass --model: the model is detected from the Copilot Chat log")

    # 1. log (once)
    if already_logged(first_prompt_text(rest)):
        print("finish: this prompt is already logged since the last commit; not logging it again")
    else:
        result = subprocess.run([sys.executable, "-B", os.path.join(HERE, "ai_log.py"), "add", *rest],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(result.stdout.strip())
        if result.returncode != 0:
            fail("the log entry was not written, so nothing was committed. Fix the problem above and run the same command again.")

    # 2. commit
    if own.no_commit:
        print("finish: --no-commit given, not committing")
        return
    changed = work_changed()
    if not changed:
        print("finish: only the AI log changed, so nothing is committed (the log goes into the next commit)")
        return
    subprocess.run(["git", "add", "-A"], check=True)
    message = f"{own.type}: {what}"
    result = subprocess.run(["git", "commit", "-m", message, "-m", f"Why: {why}"])
    if result.returncode != 0:
        fail("the commit was blocked (see the hook output above). Fix the cause, then run this same command again; "
             "the prompt will not be logged twice. Never use --no-verify.")
    print(f"finish: committed {ai_log.git('rev-parse', '--short', 'HEAD')} {message}")


if __name__ == "__main__":
    main()
