#!/usr/bin/env python3
"""Lint the step prompts in .github/prompts so a typo cannot silently break logging, committing or the demo.

Usage: python scripts/check_prompts.py        (exit 1 on any error)
"""
import glob, os, re, sys

sys.dont_write_bytecode = True  # do not leave __pycache__ files in the repo

PROMPT_DIR = os.path.join(".github", "prompts")
STEPS = ["1-spec", "2-single-approver", "3-two-approver", "4-strengthen-tests", "5-e2e-ui", "6-review-pr", "7-write-up"]
COMMITS = set(STEPS)
LOGS = set(STEPS)
WORKSHOP = "Review this PR against our checklist. Report findings by severity with file and line, suggest a fix for each, and say what you are unsure about."


def main():
    errors = []
    for name in STEPS:
        path = os.path.join(PROMPT_DIR, name + ".prompt.md")
        if not os.path.exists(path):
            errors.append(f"{name}: file missing")
            continue
        text = open(path, encoding="utf-8").read()
        front = re.match(r"---\ndescription: (.+)\nmode: agent\n---\n", text)
        if not front:
            errors.append(f"{name}: front matter must be 'description: ...' and 'mode: agent'")
        if "## Done when" not in text:
            errors.append(f"{name}: missing a '## Done when' section")
        lines = len(text.splitlines())
        if lines > 50:
            errors.append(f"{name}: {lines} lines is too long; keep step prompts under 50 (shared rules live in copilot-instructions.md)")
        for command in re.findall(r"`(python3? scripts/ai_log\.py add[^`]*)`", text):
            if "--model" in command:
                errors.append(f"{name}: a log command passes --model; the model is detected automatically")
        if name in LOGS:
            if "## Finish" not in text:
                errors.append(f"{name}: missing '## Finish'")
            if "Finish protocol" not in text:
                errors.append(f"{name}: the Finish section must point to the Finish protocol in copilot-instructions.md")
            if f"--prompt-ref {name}" not in text:
                errors.append(f"{name}: log command must use --prompt-ref {name}")
        if name in COMMITS:
            for needle in ("git add -A", "git commit -m", '"Why:'):
                if needle not in text:
                    errors.append(f"{name}: commit step is missing '{needle}'")
        for needle in ("scripts/ai_log.py", "scripts/hooks/validate-findings.py"):
            if needle in text and not os.path.exists(needle):
                errors.append(f"{name}: refers to {needle} which does not exist")
    instr = os.path.join(".github", "copilot-instructions.md")
    if not os.path.exists(instr):
        errors.append("missing .github/copilot-instructions.md")
    else:
        itext = open(instr, encoding="utf-8").read()
        for needle in ("## Finish protocol", "--parent last", "--no-verify", "Never pass `--model`", "git commit -m", "annotate last"):
            if needle not in itext:
                errors.append(f"copilot-instructions.md: Finish protocol is missing '{needle}'")
    # skills: valid front matter, short, and each custom skill is used somewhere
    custom = ["approval-rules", "approval-tests", "playwright-e2e", "review-findings", "ai-log"]
    used = ""
    for path in glob.glob(os.path.join(PROMPT_DIR, "[0-9]-*.prompt.md")) + glob.glob(os.path.join(".github", "agents", "*.md")) + [os.path.join(".github", "copilot-instructions.md")]:
        if os.path.exists(path):
            used += open(path, encoding="utf-8").read()
    for name in custom:
        path = os.path.join(".github", "skills", name, "SKILL.md")
        if not os.path.exists(path):
            errors.append(f"skill {name}: {path} is missing")
            continue
        text = open(path, encoding="utf-8").read()
        front = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", text)
        if not front or front.group(1).strip() != name:
            errors.append(f"skill {name}: front matter must start with 'name: {name}' and a 'description:'")
        elif len(front.group(2)) < 60:
            errors.append(f"skill {name}: the description must say what it does and when to use it (60+ characters)")
        if len(text.splitlines()) > 60:
            errors.append(f"skill {name}: over 60 lines; keep skills short")
        if f".github/skills/{name}/SKILL.md" not in used and f"`{name}`" not in used:
            errors.append(f"skill {name}: no prompt, agent or instruction mentions it")
    for path in glob.glob(os.path.join(PROMPT_DIR, "[0-9]-*.prompt.md")):
        for ref in re.findall(r"\.github/skills/([\w-]+)/SKILL\.md", open(path, encoding="utf-8").read()):
            if not os.path.exists(os.path.join(".github", "skills", ref, "SKILL.md")):
                errors.append(f"{os.path.basename(path)}: refers to skill {ref} which does not exist")
    review = os.path.join(PROMPT_DIR, "6-review-pr.prompt.md")
    if os.path.exists(review) and WORKSHOP not in open(review, encoding="utf-8").read():
        errors.append("6-review-pr: must keep the workshop review sentence word for word")
    e2e = os.path.join(PROMPT_DIR, "5-e2e-ui.prompt.md")
    if os.path.exists(e2e) and "refused" not in open(e2e, encoding="utf-8").read():
        errors.append("5-e2e-ui: must tell Copilot to put the word 'refused' in the refusal test title (the demo runs -g refused)")
    if os.path.exists(os.path.join(PROMPT_DIR, "2-single-approver.prompt.md")) and "README.md" not in open(os.path.join(PROMPT_DIR, "2-single-approver.prompt.md"), encoding="utf-8").read():
        errors.append("2-single-approver: must update README.md (demo accounts)")
    for path in glob.glob(os.path.join(PROMPT_DIR, "[0-9]-*.prompt.md")):
        if os.path.basename(path).replace(".prompt.md", "") not in STEPS:
            errors.append(f"{os.path.basename(path)}: not in the step list of check_prompts.py")
    # every prompt must load through the logger's own reader
    sys.path.insert(0, "scripts")
    try:
        import ai_log
        for name in STEPS:
            ai_log.load_prompt_ref(name)
    except SystemExit as exc:
        errors.append(f"logger could not load a prompt: {exc}")
    for error in errors:
        print("error:", error, file=sys.stderr)
    if errors:
        sys.exit(1)
    print(f"{len(STEPS)} prompts OK")


if __name__ == "__main__":
    main()
